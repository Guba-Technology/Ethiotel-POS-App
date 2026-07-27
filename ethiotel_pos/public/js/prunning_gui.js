window.init_pruning_manager = function(wrapper, page) {
    $(".navbar").hide();
    $(".page-head").hide();
    $(".sidebar-left").hide();
    $(".layout-side-section").hide();
    $(".page-container").css("padding-top", "0px");
    $(wrapper).find(".layout-main-section-wrapper").css({"padding": "0", "margin": "0"});
    $(wrapper).find(".layout-main-section").css({"padding": "0", "max-width": "100%", "height": "100vh"});

    const inject_assets = () => {
        const assets = [
            "https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css",
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css",
            "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700;900&display=swap"
        ];
        assets.forEach(url => {
            if (!$(`link[href="${url}"]`).length) {
                $('head').append(`<link rel="stylesheet" href="${url}">`);
            }
        });
    };
    inject_assets();

    const $root = $('<div id="vue-app-root"></div>').appendTo(page.main);

    const start_app = (VueLib) => {
        const { createApp } = VueLib;

        createApp({
            data() {
                return {
                    loading: true,
                    processing: false,
                    is_lite: false,
                    current_view: 'dashboard',
                    search_query: '',
                    workspaces: [],
                    modules: [],
                    selected_ws: [],
                    selected_mod: [],
                    tier: "ERP - Lite Admin",
                    modal: {
                        show: false,
                        title: '',
                        message: '',
                        confirm_text: 'Confirm',
                        action: null
                    },
                    toasts: [] 
                }
            },
            computed: {
                filtered_modules() {
                    return this.modules.filter(m => m.toLowerCase().includes(this.search_query.toLowerCase()));
                },
                filtered_workspaces() {
                    return this.workspaces.filter(w => w.toLowerCase().includes(this.search_query.toLowerCase()));
                }
            },
            template: `
                <div class="et-full-app">
                    
                    <div v-if="modal.show" class="et-modal-backdrop">
                        <div class="et-modal-box fade-in">
                            <div class="et-modal-header">
                                <i class="fa fa-exclamation-triangle text-warning mr-2"></i> {{ modal.title }}
                            </div>
                            <div class="et-modal-body">
                                {{ modal.message }}
                            </div>
                            <div class="et-modal-footer">
                                <button @click="modal.show = false" class="btn btn-secondary mr-2">Cancel</button>
                                <button @click="execute_modal_action" class="et-btn-et">{{ modal.confirm_text }}</button>
                            </div>
                        </div>
                    </div>

                    <div class="et-toast-container">
                        <div v-for="(t, index) in toasts" :key="index" class="et-toast fade-in">
                            <div class="d-flex align-items-center">
                                <i :class="['fa mr-2', t.icon]"></i>
                                <strong>{{ t.msg }}</strong>
                            </div>
                        </div>
                    </div>

                    <div v-if="processing" class="et-overlay">
                        <div class="text-center text-white">
                            <div class="spinner-border text-warning mb-3" style="width: 3rem; height: 3rem;"></div>
                            <h4>RECONFIGURING SYSTEM NODES...</h4>
                            <p class="text-warning">Please wait, modifying database metadata.</p>
                        </div>
                    </div>

                    <nav class="et-header">
                        <div class="et-brand-box">
                            <div class="et-logo-icon"><i class="fa fa-bolt"></i></div>
                            <div class="et-brand-text">
                                <span class="d-block font-weight-bold" style="line-height:1; font-size: 18px;">GUBA TECHNOLOGIES</span>
                                <small class="text-warning font-weight-bold" style="font-size: 10px; letter-spacing: 1px;">Module Management</small>
                            </div>
                        </div>

                        <div class="et-nav-pills">
                            <div :class="['et-pill', {active: current_view === 'dashboard'}]" @click="current_view = 'dashboard'">DASHBOARD</div>
                            <div :class="['et-pill', {active: current_view === 'workspaces'}]" @click="current_view = 'workspaces'">WORKSPACES</div>
                            <div :class="['et-pill', {active: current_view === 'modules'}]" @click="current_view = 'modules'">MODULES</div>
                        </div>

                        <div class="d-flex align-items-center">
                            <div :class="['et-mode-indicator', is_lite ? 'mode-lite' : 'mode-full']">
                                <i class="fa fa-circle mr-2"></i> {{ is_lite ? 'LITE MODE' : 'FULL CAPACITY' }}
                            </div>
                            <button @click="exit_app" class="btn-exit" title="Return to Home"><i class="fa fa-power-off"></i></button>
                        </div>
                    </nav>

                    <div class="et-main-content">
                        <div v-if="loading" class="text-center py-5 mt-5">
                            <div class="spinner-grow text-primary"></div>
                            <p class="mt-3 text-muted font-weight-bold">CONNECTING TO DATA CENTER...</p>
                        </div>

                        <div v-else class="container-fluid fade-in">
                            <div v-if="current_view === 'dashboard'" class="row">
                                <div class="col-md-4">
                                    <div class="et-card text-center h-100">
                                        <div class="et-card-head">Infrastructure Status</div>
                                        <div class="et-display-val">{{ tier }}</div>
                                        <div class="my-4">
                                            <i class="fa fa-server fa-4x text-light"></i>
                                        </div>
                                        <hr>
                                        <div class="row">
                                            <div class="col-6"><h5>{{ selected_ws.length }}</h5><small class="text-muted">Allowed WS</small></div>
                                            <div class="col-6"><h5>{{ selected_mod.length }}</h5><small class="text-muted">Active Mods</small></div>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-8">
                                    <div class="et-card h-100">
                                        <h4 class="font-weight-bold mb-3 text-primary">Optimization Gateway</h4>
                                        <p class="text-muted mb-4">You are currently running in <strong>{{ is_lite ? 'Lite' : 'Full' }}</strong> mode.</p>
                                        
                                        <div class="mode-action-box p-4 bg-light border rounded">
                                            <div v-if="!is_lite">
                                                <h5 class="text-dark"><i class="fa fa-compress mr-2"></i>Pruning Available</h5>
                                                <p class="small">Reducing system footprint will hide {{ modules.length - selected_mod.length }} modules.</p>
                                                <button @click="ask_confirmation('lite')" class="et-btn-et mt-2">
                                                    INITIALIZE LITE MODE
                                                </button>
                                            </div>
                                            <div v-else>
                                                <h5 class="text-success"><i class="fa fa-expand mr-2"></i>Restore Capacity</h5>
                                                <p class="small">Restoring will bring back all system Workspaces and Module definitions.</p>
                                                <button @click="ask_confirmation('full')" class="et-btn-outline-et mt-2">
                                                    RESTORE FULL SYSTEM
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div v-else>
                                <div class="d-flex justify-content-between align-items-center mb-4">
                                    <div class="et-search-bar">
                                        <i class="fa fa-search"></i>
                                        <input type="text" v-model="search_query" class="form-control" placeholder="Search components...">
                                    </div>
                                    <button @click="save_config" class="et-btn-et px-4 shadow-sm" :disabled="processing">
                                        <i class="fa fa-save mr-2"></i>SAVE MANIFEST
                                    </button>
                                </div>

                                <div v-if="current_view === 'workspaces'" class="et-workspace-grid">
                                    <div v-for="ws in filtered_workspaces" :key="ws" 
                                         :class="['et-ws-box', {selected: selected_ws.includes(ws)}]"
                                         @click="toggle_ws(ws)">
                                        <div class="ws-icon"><i class="fa fa-th-large"></i></div>
                                        <div class="ws-name">{{ ws }}</div>
                                        <div class="ws-indicator" v-if="selected_ws.includes(ws)"><i class="fa fa-check-circle"></i></div>
                                    </div>
                                </div>

                                <div v-if="current_view === 'modules'" class="et-module-list">
                                    <div v-for="mod in filtered_modules" :key="mod" class="et-mod-item">
                                        <div class="d-flex align-items-center">
                                            <input type="checkbox" v-model="selected_mod" :value="mod" class="custom-check" @change="notify_change(mod)">
                                            <div class="ml-3 font-weight-bold">{{ mod }}</div>
                                        </div>
                                        <div class="et-actions">
                                            <button @click="quick_toggle(mod, 1)" class="btn-lock" title="Quick Lock"><i class="fa fa-lock"></i></button>
                                            <button @click="quick_toggle(mod, 0)" class="btn-unlock" title="Quick Unlock"><i class="fa fa-unlock"></i></button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <footer class="et-footer">
                        <div>© 2026 GUBA TECHNOLOGIES | INFRASTRUCTURE DIVISION</div>
                        <div class="text-warning font-weight-bold">FRAPPE_V15_OPTIMIZED</div>
                    </footer>
                </div>
            `,
            mounted() { this.load(); },
            methods: {
                show_toast(msg, icon="fa-info-circle") {
                    this.toasts.push({msg, icon});
                    setTimeout(() => { this.toasts.shift(); }, 3000);
                },
                load() {
                    this.loading = true;
                    frappe.call('ethiotel_pos.prunning.get_init_data').then(r => {
                        this.workspaces = r.message.workspaces || [];
                        this.modules = r.message.modules || [];
                        this.selected_ws = r.message.settings.allowed_workspaces || [];
                        this.selected_mod = r.message.settings.lite_modules || [];
                        this.is_lite = r.message.is_lite === 'LITE'? true : false;
                        this.loading = false;
                    });
                },
                toggle_ws(ws) {
                    const idx = this.selected_ws.indexOf(ws);
                    if (idx > -1) {
                        this.selected_ws.splice(idx, 1);
                        this.show_toast(`Workspace Removed: ${ws}`, "fa-minus-circle");
                    } else {
                        this.selected_ws.push(ws);
                        this.show_toast(`Workspace Added: ${ws}`, "fa-plus-circle");
                    }
                },
                notify_change(mod) {
                    if(this.selected_mod.includes(mod)) {
                        this.show_toast(`Module Active: ${mod}`, "fa-check");
                    } else {
                        this.show_toast(`Module Hidden: ${mod}`, "fa-ban");
                    }
                },
                save_config() {
                    this.processing = true;
                    frappe.call({
                        method: 'ethiotel_pos.prunning.save_settings',
                        args: { 
                            workspaces: JSON.stringify(this.selected_ws), 
                            modules: JSON.stringify(this.selected_mod) 
                        },
                        callback: (r) => {
                            this.processing = false;
                            this.show_toast("Manifest Saved Successfully", "fa-save");
                        }
                    });
                },
                quick_toggle(mod, hide) {
                    frappe.call({
                        method: 'ethiotel_pos.prunning.toggle_module_visibility_from_gui',
                        args: { module_name: mod, hide: hide },
                        freeze: true,
                        callback: () => {
                            const action = hide ? "Locked (Hidden)" : "Unlocked (Visible)";
                            this.show_toast(`${mod} is now ${action}`, hide ? "fa-lock" : "fa-unlock");
                            this.load();
                        }
                    });
                },
                ask_confirmation(mode) {
                    this.modal.title = mode === 'lite' ? 'Initialize Lite Mode' : 'Restore Full System';
                    this.modal.message = mode === 'lite' 
                        ? "Are you sure you want to shrink the system? This will hide non-selected components and clear the cache." 
                        : "Are you sure you want to restore all components? This will unhide all Workspaces and Modules.";
                    this.modal.confirm_text = mode === 'lite' ? 'Yes, Shrink System' : 'Yes, Restore All';
                    this.modal.show = true;
                    this.modal.action = () => this.run_backend(mode);
                },
                execute_modal_action() {
                    if (this.modal.action) this.modal.action();
                    this.modal.show = false;
                },
                run_backend(mode) {
                    this.processing = true;
                    frappe.call({
                        method: 'ethiotel_pos.prunning.run', 
                        args: { mode: mode },
                        callback: (r) => {
                            this.processing = false;
                            this.show_toast(`System switched to ${mode.toUpperCase()} mode`, "fa-check-circle");
                            
                            setTimeout(() => {
                                this.load();
                                window.location.reload(); 
                            }, 1000);
                        }
                    });
                },
                exit_app() {
                    window.location.href = "/app/home";
                }
            }
        }).mount('#vue-app-root');
    };

    const style = `
        <style>
            body, .et-full-app { font-family: 'Roboto', sans-serif; background: #f0f3f5; overflow: hidden; }
            .et-full-app { display: flex; flex-direction: column; height: 100vh; width: 100vw; position: fixed; top: 0; left: 0; z-index: 99999; }
            
            /* Z-Index Hierarchy: App=99999, Loading=100000, Modal=100001, Toast=100002 */
            .et-overlay { position: absolute; top:0; left:0; width:100%; height:100%; background: rgba(0,84,166,0.85); z-index: 100000; display:flex; align-items:center; justify-content:center; backdrop-filter: blur(4px); }

            /* MODAL STYLES */
            .et-modal-backdrop { position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.6); z-index: 100001; display:flex; align-items:center; justify-content:center; }
            .et-modal-box { background: white; width: 500px; border-radius: 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); overflow: hidden; }
            .et-modal-header { background: #0054a6; color: white; padding: 15px 20px; font-weight: bold; font-size: 16px; display:flex; align-items:center; }
            .et-modal-body { padding: 30px 20px; color: #333; font-size: 14px; line-height: 1.5; }
            .et-modal-footer { background: #f8f9fa; padding: 15px 20px; text-align: right; border-top: 1px solid #eee; }

            /* TOAST STYLES */
            .et-toast-container { position: fixed; bottom: 60px; right: 20px; z-index: 100002; display: flex; flex-direction: column; gap: 10px; }
            .et-toast { background: #333; color: white; padding: 12px 20px; border-radius: 4px; font-size: 13px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); border-left: 4px solid #ffcc00; min-width: 250px; }

            .et-header { background: #0054a6; height: 75px; display: flex; align-items: center; justify-content: space-between; padding: 0 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.25); }
            .et-brand-box { display: flex; align-items: center; color: white; }
            .et-logo-icon { width: 45px; height: 45px; background: #ffcc00; color: #0054a6; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 22px; margin-right: 15px; }
            
            .et-nav-pills { display: flex; background: rgba(0,0,0,0.2); border-radius: 30px; padding: 5px; }
            .et-pill { color: #fff; padding: 8px 28px; border-radius: 25px; cursor: pointer; font-weight: 700; font-size: 12px; transition: 0.3s; opacity: 0.7; }
            .et-pill.active { background: #ffcc00; color: #0054a6; opacity: 1; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }

            .et-mode-indicator { font-size: 11px; font-weight: 900; padding: 7px 18px; border-radius: 20px; color: white; margin-right: 20px; letter-spacing: 0.5px; }
            .mode-lite { background: #ffcc00; color: #0054a6; }
            .mode-full { background: #28a745; }
            
            .btn-exit { background: rgba(255,255,255,0.1); border: none; color: white; width: 40px; height: 40px; border-radius: 50%; cursor: pointer; transition: 0.3s; }
            .btn-exit:hover { background: #ff4444; transform: rotate(90deg); }

            .et-main-content { flex: 1; padding: 40px; overflow-y: auto; background-image: linear-gradient(#f0f3f5 0%, #e2e8f0 100%); }
            .et-card { background: #fff; border-radius: 12px; padding: 35px; border-top: 6px solid #0054a6; box-shadow: 0 8px 25px rgba(0,0,0,0.06); margin-bottom: 30px; transition: 0.3s; }
            .et-card:hover { transform: translateY(-3px); }
            .et-card-head { color: #64748b; text-transform: uppercase; font-size: 13px; font-weight: 800; margin-bottom: 15px; letter-spacing: 1px; }
            .et-display-val { font-size: 36px; font-weight: 900; color: #0054a6; }

            .et-btn-et { background: #0054a6; color: #fff; border: none; padding: 10px 25px; border-radius: 8px; font-weight: 800; transition: 0.3s; cursor: pointer; }
            .et-btn-et:hover { background: #003366; box-shadow: 0 6px 20px rgba(0,84,166,0.4); }
            .et-btn-outline-et { background: transparent; color: #0054a6; border: 2px solid #0054a6; padding: 10px 25px; border-radius: 8px; font-weight: 800; cursor: pointer; }
            .et-btn-outline-et:hover { background: #0054a6; color: #fff; }

            .et-workspace-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 25px; }
            .et-ws-box { background: white; padding: 35px 20px; border-radius: 12px; text-align: center; cursor: pointer; border: 2px solid transparent; transition: 0.2s; position: relative; box-shadow: 0 4px 10px rgba(0,0,0,0.04); }
            .et-ws-box.selected { border-color: #0054a6; background: #f0f9ff; }
            .ws-icon { font-size: 35px; color: #0054a6; opacity: 0.5; margin-bottom: 12px; }
            .et-ws-box.selected .ws-icon { opacity: 1; }
            .ws-indicator { position: absolute; top: 12px; right: 12px; color: #0054a6; font-size: 18px; }

            .et-module-list { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 25px rgba(0,0,0,0.06); }
            .et-mod-item { display: flex; align-items: center; justify-content: space-between; padding: 22px 30px; border-bottom: 1px solid #f1f5f9; }
            .et-mod-item:hover { background: #f8fbff; }
            
            .et-actions button { background: white; border: 1px solid #e2e8f0; padding: 8px 15px; border-radius: 6px; color: #94a3b8; margin-left: 8px; transition: 0.2s; }
            .btn-lock:hover { color: #ef4444; border-color: #ef4444; background: #fef2f2; }
            .btn-unlock:hover { color: #22c55e; border-color: #22c55e; background: #f0fdf4; }

            .et-search-bar { position: relative; }
            .et-search-bar i { position: absolute; left: 18px; top: 15px; color: #0054a6; font-size: 18px; }
            .et-search-bar input { width: 400px; padding-left: 55px; height: 50px; border-radius: 10px; border: 1px solid #cbd5e1; font-weight: 500; }

            .et-footer { background: #0f172a; height: 50px; display: flex; align-items: center; justify-content: space-between; padding: 0 35px; color: #94a3b8; font-size: 12px; font-weight: 700; border-top: 1px solid #1e293b; }
            .fade-in { animation: fadeIn 0.4s ease-out; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        </style>
    `;
    $('head').append(style);

    if (window.Vue && window.Vue.createApp) {
        start_app(window.Vue);
    } else {
        frappe.require('https://unpkg.com/vue@3/dist/vue.global.prod.js', () => start_app(window.Vue));
    }
};