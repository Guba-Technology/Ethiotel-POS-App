frappe.ui.form.on('EIMS Invoice Verification', {
    onload: function(frm) {
        if(frm.doc.report_data) {
            frm.get_field('verification_summary').html(frm.doc.report_data);
            frm.refresh_field('verification_summary');
        }
        
    },
    refresh: function(frm) {
        if (frm.doc.verification_status === 'Verified') {
            frm.disable_form();
        }
        if (frm.doc.verification_status === 'Verified' && frm.doc.verification_summary) {
            frm.get_field('verification_summary').html(frm.doc.verification_summary);
        }

        if (frm.doc.verification_status !== 'Verified') {
            frm.add_custom_button(__('Fetch MoR Validation'), function() {
                
                frappe.call({
                    method: 'trigger_remote_verification',
                    doc: frm.doc,
                    freeze: true,
                    freeze_message: __('Dispatching Request to Ministry of Revenues Node...'),
                    callback: function(r) {
                        if (!r.exc && r.message) {
                            frappe.show_alert({
                                message: __('EIMS Clearance Records Successfully Synced!'),
                                indicator: 'green'
                            });
                            
                            frm.reload_doc();
                            frm.refresh();
                            setTimeout(function() {
                                attachEimsPrintHandler(frm);
                            }, 300);
                            
                            
                        }
                    }
                });
            }).addClass('btn-primary');
        }
        setTimeout(function() {
            attachEimsPrintHandler(frm);
        }, 200);
    }
});
function attachEimsPrintHandler(frm) {
 
    const wrapper = document.querySelector('[data-fieldname="verification_summary"] .control-value') ||
                    document.querySelector('[data-fieldname="verification_summary"]');

    if (!wrapper) return;

    const printBtn = wrapper.querySelector('#eims-print-btn');
    if (!printBtn) return;

    if (printBtn.getAttribute('data-eims-print-attached') === '1') return;
    printBtn.setAttribute('data-eims-print-attached', '1');

    printBtn.addEventListener('click', function() {
        const container = wrapper.querySelector('#eims-verified-container');
        if (!container) {
            frappe.msgprint({
                title: __('Print Error'),
                indicator: 'red',
                message: __('Printable receipt not found.')
            });
            return;
        }

        const printWindow = window.open('', '_blank', 'toolbar=0,location=0,menubar=0,width=900,height=700');
        if (!printWindow) {
            frappe.msgprint({
                title: __('Popup Blocked'),
                indicator: 'orange',
                message: __('Please allow popups for this site to enable printing.')
            });
            return;
        }

        const receiptHtml = container.outerHTML;

        const styles = `
            <style>
                @media print {
                    @page { size: auto; margin: 10mm; }
                    body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                }
                body {
                    font-family: 'Helvetica Neue', Arial, sans-serif;
                    color: #1f2d3d;
                    margin: 0;
                    padding: 12px;
                    background: #ffffff;
                }
                .eims-verified-container { box-shadow: none; }
                table { border-collapse: collapse; width: 100%; }
                table th, table td { border: 1px solid #e9ecef; padding: 8px; }
                .text-muted { color: #6c757d; }
                .text-success { color: #28a745; font-weight: 700; }
                .text-danger { color: #dc3545; }
                .label { display:inline-block; padding:3px 8px; border-radius:12px; background:#e9ecef; font-size:12px; }
            </style>
        `;

        printWindow.document.open();
        printWindow.document.write(`
            <!doctype html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>EIMS Tax Clearance Receipt</title>
                ${styles}
            </head>
            <body>
                ${receiptHtml}
                <script>
                    // Auto-print and close after printing (user can cancel)
                    function doPrint() {
                        try {
                            window.focus();
                            window.print();
                        } catch (e) {
                            console.error(e);
                        }
                    }
                    // Wait a short moment for fonts/images to load
                    setTimeout(doPrint, 300);
                <\/script>
            </body>
            </html>
        `);
        printWindow.document.close();
    });
}