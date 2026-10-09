from __future__ import annotations
import os
import json
import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime

# --- CONFIGURATION ---
API_URL = os.getenv('DASHBOARD_API_URL', 'http://127.0.0.1:8000').rstrip('/')
st.set_page_config(page_title='DPSO-GA Control Center', page_icon=':rocket:', layout='wide', initial_sidebar_state='expanded')

# --- CUSTOM CSS ---
def inject_custom_css():
    st.markdown('''
    <style>
    :root {
        --bg-color: #050B14;
        --card-bg: rgba(16, 24, 39, 0.7);
        --card-border: rgba(56, 189, 248, 0.1);
        --accent-cyan: #38bdf8;
        --accent-purple: #a855f7;
        --accent-green: #22c55e;
        --accent-amber: #f59e0b;
        --accent-red: #ef4444;
        --text-main: #f8fafc;
        --text-muted: #94a3b8;
    }
    .stApp {
        background-color: var(--bg-color);
        background-image: radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.05) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(168, 85, 247, 0.05) 0px, transparent 50%);
        color: var(--text-main);
    }
    .glass-card {
        background: var(--card-bg);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    .kpi-title { font-size: 0.85rem; text-transform: uppercase; color: var(--text-muted); letter-spacing: 1px; margin-bottom: 5px; }
    .kpi-value { font-size: 1.8rem; font-weight: 700; color: var(--text-main); }
    .kpi-highlight-cyan { color: var(--accent-cyan); }
    .kpi-highlight-purple { color: var(--accent-purple); }
    .kpi-highlight-green { color: var(--accent-green); }
    .kpi-highlight-amber { color: var(--accent-amber); }
    .kpi-highlight-red { color: var(--accent-red); }
    .status-dot { height: 10px; width: 10px; background-color: var(--accent-green); border-radius: 50%; display: inline-block; margin-right: 5px; box-shadow: 0 0 8px var(--accent-green); }
    .status-dot.offline { background-color: var(--accent-red); box-shadow: 0 0 8px var(--accent-red); }
    
    /* Modern App Sidebar Navigation */
    [data-testid="stSidebar"] [data-testid="baseButton-secondary"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: var(--text-muted) !important;
        justify-content: flex-start !important;
        padding-left: 15px !important;
        transition: all 0.2s ease;
    }
    [data-testid="stSidebar"] [data-testid="baseButton-secondary"]:hover {
        background-color: rgba(56, 189, 248, 0.1) !important;
        color: var(--text-main) !important;
    }
    [data-testid="stSidebar"] [data-testid="baseButton-primary"] {
        background: linear-gradient(90deg, rgba(56,189,248,0.2) 0%, transparent 100%) !important;
        border: none !important;
        border-left: 3px solid var(--accent-cyan) !important;
        box-shadow: none !important;
        color: var(--accent-cyan) !important;
        justify-content: flex-start !important;
        padding-left: 12px !important;
        font-weight: 600 !important;
        border-radius: 0 8px 8px 0 !important;
    }
    </style>
    ''', unsafe_allow_html=True)

# --- HELPERS ---
def api_get(path, **params):
    with httpx.Client(timeout=10) as client:
        response = client.get(f'{API_URL}{path}', params=params)
        response.raise_for_status()
        return response.json()

def api_post(path, payload=None, files=None, **params):
    with httpx.Client(timeout=600) as client:
        response = client.post(f'{API_URL}{path}', json=payload, files=files, params=params)
        if response.status_code >= 400:
            try:
                detail = response.json().get('detail', response.text)
                raise ValueError(detail)
            except Exception as e:
                if isinstance(e, ValueError): raise e
                raise ValueError(f"HTTP {response.status_code}: {response.text}")
        return response.json()

def check_health():
    try:
        h = api_get('/health')
        return True, h.get('status', 'Unknown')
    except Exception:
        return False, 'Offline'

# --- RENDER COMPONENTS ---
def render_header(is_online, status_text):
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title('DPSO-GA')
        st.subheader('Intelligent Cloud Resource Optimization')
        st.caption('CNN-LSTM Forecasting - GA / PSO / Hybrid PSO-GA - Intelligent Auto-Scaling')
    with col2:
        dot_class = 'status-dot' if is_online else 'status-dot offline'
        status_msg = 'SYSTEM ONLINE' if is_online else 'SYSTEM OFFLINE'
        st.markdown(f'''
        <div style="text-align: right;">
            <div><span class="{dot_class}"></span><b>{status_msg}</b></div>
            <div style="color: var(--text-muted); font-size: 0.9em; margin-top: 5px;">API: {API_URL}</div>
            <div style="color: var(--text-muted); font-size: 0.9em;">Mode: {st.session_state.get("mode", "simulation").upper()}</div>
        </div>
        ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_kpi_card(title, value, color_class=""):
    return f'''
    <div class="glass-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value {color_class}">{value}</div>
    </div>
    '''

def render_command_center():
    st.markdown('### COMMAND CENTER')
    
    st.markdown('''
    <div style="background: rgba(16, 24, 39, 0.7); border: 1px solid rgba(56, 189, 248, 0.2); padding: 15px; border-radius: 12px; margin-bottom: 25px; text-align: center; color: var(--accent-cyan);">
        <b>WORKLOAD</b> -> <b>ANALYSIS</b> -> <b>CNN-LSTM</b> -> <b>GA / PSO / PSO-GA</b> -> <b>DECISION ENGINE</b> -> <b>RESOURCE SCALING</b> -> (Feedback Loop)
    </div>
    ''', unsafe_allow_html=True)
    
    cols = st.columns(5)
    
    wrk = st.session_state.get('workload_result', {})
    analysis = wrk.get('analysis', {})
    intensity = analysis.get('workload_intensity', 0.0)
    pred_demand = analysis.get('estimated_future_demand', 0.0)
    sys_health = 'HEALTHY'
    if analysis.get('classification') in ['HIGH', 'OVERLOADED']: sys_health = 'WARNING'
    
    dec = st.session_state.get('decision_result', {})
    cur_cap = dec.get('current_capacity', '-')
    rec_cap = dec.get('recommended_capacity', '-')
    action = dec.get('scaling_action', '-')
    
    opt = st.session_state.get('optimization_result', {})
    winner = opt.get('winner', {}).get('algorithm', '-').upper()
    
    with cols[0]: st.markdown(render_kpi_card('Workload', f'{intensity:.2f}'), unsafe_allow_html=True)
    with cols[1]: st.markdown(render_kpi_card('Predicted', f'{pred_demand:.2f}'), unsafe_allow_html=True)
    with cols[2]: st.markdown(render_kpi_card('Optimizer', winner, 'kpi-highlight-purple'), unsafe_allow_html=True)
    with cols[3]: 
        action_color = 'kpi-highlight-green' if action == 'MAINTAIN' else 'kpi-highlight-amber'
        st.markdown(render_kpi_card('Action', action, action_color), unsafe_allow_html=True)
    with cols[4]:
        health_color = 'kpi-highlight-green' if sys_health == 'HEALTHY' else 'kpi-highlight-red'
        st.markdown(render_kpi_card('Health', sys_health, health_color), unsafe_allow_html=True)
        
    st.divider()

def render_workload():
    st.markdown('### WORKLOAD INTELLIGENCE')
    col1, col2 = st.columns([1, 2])
    with col1:
        uploaded = st.file_uploader('Upload Workload Dataset (CSV)', type=['csv'])
        if uploaded:
            if st.button('RUN INTELLIGENT ANALYSIS'):
                with st.spinner('Analyzing workload...'):
                    try:
                        data = api_post('/api/workload/upload', files={'file': (uploaded.name, uploaded.getvalue(), 'text/csv')}, seed=st.session_state.seed)
                        st.session_state['workload_result'] = data['result']
                        if 'prediction' in data['result']:
                            st.session_state['prediction_result'] = data['result']['prediction']
                        st.success('Dataset validated and analyzed successfully.')
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Dataset validation failed: {exc}")
                        
        st.markdown("#### Synthetic Profile")
        if st.button('Analyze selected workload profile'):
            with st.spinner('Analyzing profile...'):
                try:
                    data = api_post('/api/workload/analyze', {'source': st.session_state.source, 'seed': st.session_state.seed})
                    st.session_state['workload_result'] = data['result']
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
                    
    with col2:
        wrk = st.session_state.get('workload_result')
        if wrk:
            an = wrk.get('analysis', {})
            cl1, cl2, cl3 = st.columns(3)
            cl1.metric('Classification', an.get('classification'))
            cl2.metric('Intensity', f"{an.get('workload_intensity',0):.3f}")
            cl3.metric('Volatility', f"{an.get('workload_volatility',0):.3f}")
            
            if 'preview' in wrk:
                df = pd.DataFrame(wrk['preview'])
                if 'timestamp' in df.columns:
                    st.line_chart(df.set_index('timestamp')[['cpu', 'memory', 'network']])
                else:
                    st.line_chart(df[['cpu', 'memory', 'network']])
        else:
            st.info("No workload analyzed yet. Upload a dataset or run a synthetic profile.")

def render_prediction():
    st.markdown('### AI DEMAND FORECAST')
    if st.button('Force Analyze & Predict'):
        with st.spinner('Running CNN-LSTM Prediction...'):
            try:
                if 'workload_result' not in st.session_state:
                    api_post('/api/workload/analyze', {'source': st.session_state.source, 'seed': st.session_state.seed})
                data = api_post('/api/workload/predict', {'source': st.session_state.source, 'seed': st.session_state.seed})
                st.session_state['prediction_result'] = data['result']
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
                
    pred = st.session_state.get('prediction_result')
    if pred:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(render_kpi_card('Baseline Error (MAE)', f"{pred.get('baseline_mae',0):.4f}"), unsafe_allow_html=True)
        with col2:
            st.markdown(render_kpi_card('Optimized Error (MAE)', f"{pred.get('optimized_mae',0):.4f}", "kpi-highlight-cyan"), unsafe_allow_html=True)
            
        st.markdown("#### Forecast vs Actual")
        try:
            chart_df = pd.DataFrame({'Actual': pred['actual_tail'], 'Predicted': pred['predicted_tail']})
            fig = px.line(chart_df, title="Workload Tail Verification", markers=True, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            chart = pd.DataFrame({'actual': pred['actual_tail'], 'predicted': pred['predicted_tail']})
            st.line_chart(chart)
            
        with st.expander("Model Configuration & Parameters"):
            st.json(pred.get('optimized_parameters', {}))
    else:
        st.info("No prediction data available. Run analysis on a dataset with enough rows.")

def render_optimization():
    st.markdown('### OPTIMIZATION ARENA')
    if st.button('Run Optimization Strategy (GA vs PSO vs PSO-GA)'):
        with st.spinner('Running population-based optimizers...'):
            try:
                data = api_post('/api/optimize', {'tasks': st.session_state.tasks, 'vms': st.session_state.vms, 'seed': st.session_state.seed, 'population_size': 24, 'iterations': 20})
                st.session_state['optimization_result'] = data['result']
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
                
    opt = st.session_state.get('optimization_result')
    if opt:
        table = pd.DataFrame(opt['results'])
        winner = opt['winner']['algorithm'].upper()
        st.markdown(render_kpi_card('OPTIMIZATION WINNER', winner, "kpi-highlight-purple"), unsafe_allow_html=True)
        st.caption("Best optimization result based on the configured fitness function.")
        
        st.dataframe(table, use_container_width=True)
        
        try:
            fig = px.bar(table, x='algorithm', y=['fitness', 'makespan', 'energy'], barmode='group', title="Algorithm Performance Comparison", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.bar_chart(table.set_index('algorithm')[['fitness', 'makespan']])
    else:
        st.info("Run optimization to compare algorithms.")

def render_decision():
    st.markdown('### RESOURCE DECISION CENTER')
    
    # Get current capacity from the autoscaler to keep it synced
    try:
        active_vms = api_get('/api/autoscaling/status').get('active', 3)
    except:
        active_vms = 3
        
    current_capacity = st.number_input('Current running instances', min_value=1, value=int(active_vms), step=1)
    if st.button('Generate & Execute Decision'):
        with st.spinner('Calculating and executing scaling recommendation...'):
            try:
                data = api_post('/api/decisions', {'current_capacity': int(current_capacity), 'minimum_capacity': 1, 'maximum_capacity': 20, 'safe_utilization': .75, 'dry_run': st.session_state.dry_run})
                st.session_state['decision_result'] = data['result']
                
                # Automatically execute the scaling action right away
                recommended = data['result']['recommended_capacity']
                api_post('/api/autoscaling/scale', {"target_capacity": recommended, "reason": "Decision Center Auto-Execution"})
                
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
                
    dec = st.session_state.get('decision_result')
    if dec:
        st.markdown(f"**Explanation:** {dec['reason']}")
        cols = st.columns(4)
        cols[0].metric('CURRENT', f"{dec['current_capacity']} VMs")
        cols[1].metric('PREDICTED DEMAND', f"{dec['predicted_demand']:.3f}")
        cols[2].metric('RECOMMENDED', f"{dec['recommended_capacity']} VMs")
        
        action = dec['scaling_action']
        arrow = "UP" if action == "SCALE OUT" else "DOWN" if action == "SCALE IN" else "-"
        color = "red" if action == "SCALE OUT" else "cyan" if action == "SCALE IN" else "green"
        cols[3].markdown(f"<h3 style='color:{color}'>{arrow} {action}</h3>", unsafe_allow_html=True)
    else:
        st.info("Generate a decision to view scaling recommendations.")

def render_autoscaling():
    st.markdown('### AUTOSCALING DASHBOARD')
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Refresh Status'):
            st.rerun()
            
    with col2:
        with st.popover("Manual Scale"):
            target = st.number_input("Target VMs", min_value=1, max_value=20, value=3)
            if st.button("Execute Scaling"):
                try:
                    res = api_post('/api/autoscaling/scale', {"target_capacity": target, "reason": "Manual dashboard request"})
                    st.success(f"Action: {res.get('action')}")
                except Exception as exc:
                    st.error(str(exc))
                    
    try:
        status = api_get('/api/autoscaling/status')
        cols = st.columns(4)
        cols[0].metric("Total VMs", status.get("total", 0))
        cols[1].metric("Active VMs", status.get("active", 0))
        
        vms = api_get('/api/autoscaling/vms')
        if vms:
            st.markdown("#### Virtual Machines")
            df_vms = pd.DataFrame(vms)
            st.dataframe(df_vms, use_container_width=True)
            
        history = api_get('/api/autoscaling/history')
        if history:
            st.markdown("#### Scaling History")
            df_hist = pd.DataFrame(history)
            st.dataframe(df_hist, use_container_width=True)
            
    except Exception as exc:
        st.warning(f"Could not load autoscaling data: {exc}")

def render_cloud():
    st.markdown('### CLOUD INFRASTRUCTURE')
    mode = st.session_state.mode
    st.write(f"**Provider:** {'Local Simulation' if mode == 'simulation' else 'AWS'}")
    st.write(f"**Connection:** {'Connected' if mode == 'simulation' else 'Not Connected'}")
    st.write(f"**Execution:** {'Dry Run' if st.session_state.dry_run else 'Live'}")
    
    if st.button('Check Cloud Status'):
        try:
            res = api_get('/api/cloud/status', mode=mode, dry_run=st.session_state.dry_run)
            st.json(res)
        except Exception as exc:
            st.error(str(exc))
            
    if mode != 'simulation':
        st.warning("AWS NOT CONNECTED. (Credentials or infrastructure missing. Local simulation remains available.)")

def render_research():
    st.markdown('### RESEARCH & EXPERIMENT HISTORY')
    st.write("View historical optimization results.")
    if st.button("Load Phase 1 & 2 Results"):
        try:
            p1 = api_get('/api/results/phase1')
            if p1.get('status') == 'available': 
                st.markdown("#### Phase 1: Optimizer Metrics")
                st.dataframe(pd.DataFrame(p1['result']), use_container_width=True)
                
            p2 = api_get('/api/results/phase2')
            if p2.get('status') == 'available':
                st.markdown("#### Phase 2: Configuration")
                st.json(p2['result'])
        except Exception as exc:
            st.warning(str(exc))
            
    st.markdown("#### System Technical Details")
    with st.expander("API Connection Status"):
        st.write(f"URL: {API_URL}")
        st.write("Session State Keys:")
        st.json(list(st.session_state.keys()))

def render_google_trace():
    st.markdown('### GOOGLE CLUSTER TRACE INTEGRATION')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Load Sample Trace"):
            with st.spinner("Parsing and normalizing Google Cluster Trace..."):
                try:
                    res = api_post('/api/workload/google-trace/load', {"file_path": "data/raw/google_cluster_trace/sample_task_usage.csv", "window_seconds": 60})
                    st.success("Trace loaded successfully!")
                except Exception as exc:
                    st.error(str(exc))
                    
    with col2:
        speed = st.number_input("Replay Speed (x)", min_value=1, value=10)
        if st.button("Start Replay"):
            try:
                api_post('/api/workload/google-trace/run', {"speed": speed})
                st.success("Replay started!")
            except Exception as e:
                st.error(str(e))
                
    with col3:
        if st.button("Pause"):
            try:
                api_post('/api/workload/google-trace/pause', {})
            except Exception as e: pass
            
        if st.button("Step Forward (1 Window)"):
            try:
                api_post('/api/workload/google-trace/step', {})
                st.success("Stepped forward.")
            except Exception as e:
                st.error(str(e))
                
    try:
        status = api_get('/api/workload/google-trace/status')
        if status.get('loaded'):
            st.markdown("#### Trace Information")
            cols = st.columns(4)
            cols[0].metric("Dataset", "Google Cluster Trace 2011 (v2)")
            cols[1].metric("Records", status.get("records"))
            cols[2].metric("Window Size", f"{status.get('window_seconds')}s")
            cols[3].metric("Position", f"{status.get('current_position')} / {status.get('records')}")
            
            st.write(f"**Status:** {'Replaying' if status.get('is_replaying') else 'Paused/Stopped'}")
            
            cw = status.get('current_workload')
            if cw:
                st.markdown("#### Current Normalized Workload")
                st.json(cw)
                
            st.markdown("#### Pipeline Integration")
            st.info("The trace workload is directly feeding into the standard CNN-LSTM → DPSO-GA → Autoscaler pipeline! Check the Autoscaling Dashboard to see the VMs reacting live.")
        else:
            st.info("No trace loaded. Click 'Load Sample Trace' to begin.")
    except Exception as e:
        st.warning(f"Could not connect to trace API: {e}")

def render_google_trace_lab():
    st.markdown('### GOOGLE TRACE LAB (Benchmark & Evaluation)')
    st.write("Evaluate GA, PSO, and DPSO-GA on the real-world Google Cluster Trace dataset.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Benchmark Configuration")
        dataset = st.text_input("Dataset Path", "data/raw/google_cluster_trace/sample_task_usage.csv")
        window_seconds = st.number_input("Time Window (seconds)", min_value=10, value=60)
        max_records = st.number_input("Max Records to Process", min_value=10, value=100)
        seed = st.number_input("Random Seed", min_value=0, value=42)
        
    with col2:
        st.markdown("#### Algorithms to Compare")
        run_ga = st.checkbox("GA (Genetic Algorithm)", value=True)
        run_pso = st.checkbox("PSO (Particle Swarm Optimization)", value=True)
        run_psoga = st.checkbox("DPSO-GA (Hybrid)", value=True)
        
        algorithms = []
        if run_ga: algorithms.append("ga")
        if run_pso: algorithms.append("pso")
        if run_psoga: algorithms.append("psoga")
        
        if st.button("RUN BENCHMARK", type="primary"):
            if not algorithms:
                st.error("Select at least one algorithm.")
                return
                
            with st.spinner("Running extensive benchmark on Google Trace... (This may take a while)"):
                try:
                    res = api_post('/api/benchmark/google-trace/run', {
                        "dataset": dataset,
                        "window_seconds": window_seconds,
                        "algorithms": algorithms,
                        "max_records": max_records,
                        "seed": seed
                    })
                    st.session_state['benchmark_result'] = res
                    st.success("Benchmark completed successfully!")
                except Exception as exc:
                    st.error(f"Benchmark failed: {exc}")
                    
    if 'benchmark_result' in st.session_state:
        res = st.session_state['benchmark_result']
        
        st.divider()
        st.markdown("#### 📊 ALGORITHM COMPARISON")
        
        # Display metadata
        md = res['metadata']
        st.caption(f"**Dataset:** {md['dataset']} ({md['data_type']}) | **Records:** {md['records']} | **Window:** {md['window_seconds']}s | **Seed:** {md['seed']}")
        
        # Display summary table
        summary = res['summary']
        df = pd.DataFrame(summary).T
        st.dataframe(df.style.highlight_min(axis=0, color='lightgreen', subset=['SLA Violations', 'Wastage', 'Cost', 'Execution Time'])
                     .highlight_max(axis=0, color='lightgreen', subset=['CPU Util.', 'Memory Util.']), use_container_width=True)
        
        # Visualizations
        st.markdown("#### Execution History")
        
        for algo in algorithms:
            if algo in res['results']:
                hist = res['results'][algo]
                with st.expander(f"{algo.upper()} VM Allocation History"):
                    chart_data = pd.DataFrame({
                        'VM Count': hist['vm_count_history'],
                        'CPU Util': hist['cpu_util_history'],
                        'Mem Util': hist['mem_util_history']
                    })
                    st.line_chart(chart_data)

# --- MAIN APP ROUTING ---
def main():
    inject_custom_css()
    is_online, status_text = check_health()
    render_header(is_online, status_text)
    
    if not is_online:
        st.error(f"Backend unavailable at {API_URL}. Please start the FastAPI backend.")
        if st.button("RECONNECT"):
            st.rerun()
        st.stop()
        
    st.sidebar.markdown("## SYSTEM CONFIG")
    st.session_state.mode = st.sidebar.selectbox('Mode', ['simulation', 'aws'])
    st.session_state.dry_run = st.sidebar.checkbox('Dry-run', value=True, disabled=(st.session_state.mode == 'simulation'))
    st.session_state.source = st.sidebar.selectbox('Workload Profile', ['E-commerce', 'Banking', 'Streaming', 'Education', 'Healthcare', 'SaaS', 'Custom'])
    st.session_state.seed = st.sidebar.number_input('Seed', min_value=0, value=42, step=1)
    st.session_state.tasks = st.sidebar.number_input('Tasks', min_value=1, value=50, step=1)
    st.session_state.vms = st.sidebar.number_input('VMs', min_value=1, value=12, step=1)
    
    st.sidebar.markdown("## NAVIGATION")
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "OVERVIEW"

    pages = [
        "OVERVIEW",
        "WORKLOAD",
        "GOOGLE TRACE",
        "GOOGLE TRACE LAB",
        "AI FORECAST",
        "OPTIMIZATION ARENA",
        "RESOURCE CONTROL",
        "AUTOSCALING",
        "CLOUD STATUS",
        "RESEARCH"
    ]

    for p in pages:
        btn_type = "primary" if st.session_state.current_page == p else "secondary"
        if st.sidebar.button(p, type=btn_type, use_container_width=True):
            st.session_state.current_page = p
            st.rerun()

    nav = st.session_state.current_page
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### DPSO-GA SYSTEM")
    st.sidebar.caption("[OK] CNN-LSTM\n[OK] GA\n[OK] PSO\n[OK] PSO-GA\n[OK] FastAPI\n[OK] Simulation\n[!] AWS Ready")
    
    if nav == "OVERVIEW":
        render_command_center()
        render_workload()
    elif nav == "WORKLOAD":
        render_workload()
    elif nav == "GOOGLE TRACE":
        render_google_trace()
    elif nav == "GOOGLE TRACE LAB":
        render_google_trace_lab()
    elif nav == "AI FORECAST":
        render_prediction()
    elif nav == "OPTIMIZATION ARENA":
        render_optimization()
    elif nav == "RESOURCE CONTROL":
        render_decision()
    elif nav == "AUTOSCALING":
        render_autoscaling()
    elif nav == "CLOUD STATUS":
        render_cloud()
    elif nav == "RESEARCH":
        render_research()

if __name__ == '__main__':
    main()
