frappe.ui.form.on('EIMS Invoice Receipt', {
    onload: function(frm) {
        frappe.call({
            doc: frm.doc,
            method: 'compile_receipt_html',
            callback: function(r) {
                if (r.message && frm.get_field('receipt_viewport')) {
                    frm.get_field('receipt_viewport').html(r.message);
                }
            }
        });
    },

    payment_entry: function(frm) {
        if (frm.doc.payment_entry && frm.doc.eims_status !== 'Active') {
            frappe.call({
                method: 'fetch_payment_entry_details',
                doc: frm.doc,
                callback: function() {
                    frm.refresh_fields();
                }
            });
        }
    },

    refresh: function(frm) {
        if (frm.doc.eims_status === 'Active' && frm.doc.qr_code_base64) {
            frm.disable_form();
            frappe.call({
                doc: frm.doc,
                method: 'compile_receipt_html',
                callback: function(r) {
                    if (r.message && frm.get_field('receipt_viewport')) {
                        frm.get_field('receipt_viewport').html(r.message);
                    }
                }
            });
        }

        if (frm.doc.eims_status !== 'Active') {
            frm.add_custom_button(__('Authorize MoR Receipt'), function() {
                frappe.call({
                    method: 'trigger_remote_receipt_generation',
                    doc: frm.doc,
                    freeze: true,
                    freeze_message: __('Transmitting Safe Receipt Declaration to Revenue Endpoint...'),
                    callback: function(r) {
                        frm.reload_doc().then(() => {
                            if (r.message && r.message.success) {
                                frappe.show_alert({
                                    message: __('EIRMS Receipt Certified and Registered Successfully!'),
                                    indicator: 'green'
                                });
                            } else if (r.message && !r.message.success) {
                                frappe.msgprint({
                                    title: __('EIRMS Gateway Rejection'),
                                    indicator: 'red',
                                    message: r.message.message
                                });
                            }
                        });
                    }
                });
            }).addClass('btn-primary');
        } else if (frm.doc.eims_status === 'Active') {
            frm.add_custom_button(__('Print Preview '), function() {
                frappe.call({
                    doc: frm.doc,
                    method: 'compile_receipt_html',
                    callback: function(r) {
                        if (!r.message) {
                            frappe.msgprint(__('No receipt HTML returned.'));
                            return;
                        }

                        var popup = window.open('', '_blank', 'toolbar=0,location=0,menubar=0,width=900,height=700');
                        if (!popup) {
                            frappe.msgprint(__('Popup blocked. Please allow popups for this site or use the inline preview.'));
                            return;
                        }

                        var doc = popup.document;
                        doc.open();

                        var headHtml = '<!doctype html><html><head><meta charset="utf-8"><title>EIRMS Receipt Preview</title>';
                        headHtml += '<style>';
                        headHtml += 'body{font-family:Arial,sans-serif;color:#000;margin:20px;}';
                        headHtml += '#popup-toolbar{position:fixed; top:12px; right:12px; z-index:9999; display:flex; gap:8px;}';
                        headHtml += '#popup-toolbar button{background:#3182ce;color:#fff;border:none;padding:8px 12px;border-radius:6px;cursor:pointer;font-weight:700;}';
                        headHtml += '#popup-toolbar button.close-btn{background:#e2e8f0;color:#1f2d3d;}';
                        headHtml += '@media print { #popup-toolbar, .inline-print-btn { display: none !important; } body { -webkit-print-color-adjust: exact; margin:0; } }';
                        headHtml += '</style></head><body>';

                        var toolbarHtml = '<div id="popup-toolbar">';
                        toolbarHtml += '<button id="popup-print">🖨️ Print</button>';
                        toolbarHtml += '<button id="popup-close" class="close-btn">Close</button>';
                        toolbarHtml += '</div>';

                        var contentWrapperStart = '<div id="popup-content" style="margin-top:48px;">';
                        var contentWrapperEnd = '</div>';

                        var scriptContent = '';
                        scriptContent += '(function(){';
                        scriptContent += '  var printBtn = document.getElementById("popup-print");';
                        scriptContent += '  var closeBtn = document.getElementById("popup-close");';
                        scriptContent += '  printBtn.addEventListener("click", function(){';
                        scriptContent += '    var imgs = document.getElementById("popup-content").getElementsByTagName("img");';
                        scriptContent += '    var total = imgs.length;';
                        scriptContent += '    if (total === 0) { window.print(); return; }';
                        scriptContent += '    var loaded = 0;';
                        scriptContent += '    var done = function(){ loaded++; if (loaded === total) { window.print(); } };';
                        scriptContent += '    for (var i=0;i<imgs.length;i++){';
                        scriptContent += '      if (imgs[i].complete) { done(); } else { imgs[i].addEventListener("load", done); imgs[i].addEventListener("error", done); }';
                        scriptContent += '    }';
                        scriptContent += '    setTimeout(function(){ window.print(); }, 1500);';
                        scriptContent += '  });';
                        scriptContent += '  closeBtn.addEventListener("click", function(){ window.close(); });';
                        scriptContent += '})();';

                        doc.write(headHtml);
                        doc.write(toolbarHtml);
                        doc.write(contentWrapperStart);
                        doc.write(r.message); 
                        doc.write(contentWrapperEnd);
                        doc.write('<scr' + 'ipt>' + scriptContent + '</scr' + 'ipt>');
                        doc.write('</body></html>');
                        doc.close();

                        popup.focus();
                    }
                });
            }).addClass('btn-info');
        }
    }
});