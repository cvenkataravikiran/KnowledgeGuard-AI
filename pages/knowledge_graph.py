"""Knowledge Graph Visualization Page"""
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network
import tempfile
from database.database import get_db
from services.knowledge_service import KnowledgeService


def show():
    st.title("🌐 Knowledge Graph")
    st.markdown("Interactive visualization of organizational knowledge relationships")
    
    db = get_db()
    
    try:
        # Sync data first
        with st.spinner("Synchronizing knowledge data..."):
            KnowledgeService.sync_employees(db, user_id=st.session_state.user_id)
            KnowledgeService.sync_systems(db, user_id=st.session_state.user_id)
            KnowledgeService.sync_projects(db, user_id=st.session_state.user_id)
            KnowledgeService.sync_mappings(db, user_id=st.session_state.user_id)
        
        # Controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_employees = st.checkbox("Show Employees", value=True)
        
        with col2:
            show_systems = st.checkbox("Show Systems", value=True)
        
        with col3:
            show_projects = st.checkbox("Show Projects", value=True)
        
        # Build graph
        if st.button("🔄 Refresh Graph", use_container_width=True):
            st.rerun()
        
        # Get graph data
        graph_data = KnowledgeService.build_knowledge_graph(db, user_id=st.session_state.user_id)
        
        if not graph_data["nodes"]:
            st.warning("No data available for knowledge graph. Upload documents and run risk analysis first.")
            return
        
        # Filter nodes based on selection
        filtered_nodes = []
        filtered_edges = []
        
        for node in graph_data["nodes"]:
            include = False
            if node["type"] == "employee" and show_employees:
                include = True
            elif node["type"] == "system" and show_systems:
                include = True
            elif node["type"] == "project" and show_projects:
                include = True
            
            if include:
                filtered_nodes.append(node)
        
        # Filter edges based on included nodes
        node_ids = {node["id"] for node in filtered_nodes}
        for edge in graph_data["edges"]:
            if edge["from"] in node_ids and edge["to"] in node_ids:
                filtered_edges.append(edge)
        
        # Create PyVis network
        net = Network(
            height="600px",
            width="100%",
            bgcolor="#ffffff",
            font_color="#000000",
            notebook=False
        )
        
        # Configure physics
        net.set_options("""
        {
            "physics": {
                "enabled": true,
                "barnesHut": {
                    "gravitationalConstant": -30000,
                    "centralGravity": 0.3,
                    "springLength": 200,
                    "springConstant": 0.04,
                    "damping": 0.09
                },
                "minVelocity": 0.75
            },
            "interaction": {
                "hover": true,
                "navigationButtons": true,
                "keyboard": true
            }
        }
        """)
        
        # Color mapping
        color_map = {
            "employee": {
                "critical": "#dc3545",
                "high": "#fd7e14",
                "medium": "#ffc107",
                "low": "#28a745",
                "unknown": "#6c757d"
            },
            "system": {
                "critical": "#6610f2",
                "high": "#e83e8c",
                "medium": "#20c997",
                "low": "#17a2b8"
            },
            "project": "#0d6efd"
        }
        
        # Add nodes
        for node in filtered_nodes:
            if node["type"] == "employee":
                color = color_map["employee"].get(node.get("risk_level", "unknown"), "#6c757d")
                title = f"Employee: {node['label']}\nRisk: {node.get('risk_level', 'unknown')}"
                shape = "dot"
            elif node["type"] == "system":
                color = color_map["system"].get(node.get("criticality", "low"), "#17a2b8")
                title = f"System: {node['label']}\nCriticality: {node.get('criticality', 'unknown')}"
                shape = "square"
            else:  # project
                color = color_map["project"]
                title = f"Project: {node['label']}\nStatus: {node.get('status', 'unknown')}"
                shape = "triangle"
            
            net.add_node(
                node["id"],
                label=node["label"],
                title=title,
                color=color,
                size=node.get("size", 15),
                shape=shape
            )
        
        # Add edges
        for edge in filtered_edges:
            width = edge.get("strength", 1.0) * 3
            color = "#0d6efd" if edge.get("is_primary") else "#adb5bd"
            
            net.add_edge(
                edge["from"],
                edge["to"],
                width=width,
                color=color,
                title=f"Type: {edge['type']}"
            )
        
        # Save and display graph (using mkstemp to avoid Windows file sharing PermissionError)
        import os
        fd, temp_path = tempfile.mkstemp(suffix=".html")
        try:
            os.close(fd) # Close file descriptor so PyVis can open/write to it
            net.save_graph(temp_path)
            with open(temp_path, 'r', encoding='utf-8') as html_file:
                html_content = html_file.read()
            components.html(html_content, height=650, scrolling=False)
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass
        
        # Legend
        st.markdown("---")
        st.subheader("📖 Legend")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Employees (Circles)**")
            st.markdown("🔴 Critical Risk")
            st.markdown("🟠 High Risk")
            st.markdown("🟡 Medium Risk")
            st.markdown("🟢 Low Risk")
        
        with col2:
            st.markdown("**Systems (Squares)**")
            st.markdown("🟣 Critical")
            st.markdown("🌺 High")
            st.markdown("🌊 Medium")
            st.markdown("🔵 Low")
        
        with col3:
            st.markdown("**Projects (Triangles)**")
            st.markdown("🔵 All Projects")
            st.markdown("")
            st.markdown("**Connections**")
            st.markdown("Thick blue = Primary owner")
            st.markdown("Thin gray = Contributor")
        
        # Graph statistics
        st.markdown("---")
        st.subheader("📊 Graph Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            employee_count = len([n for n in filtered_nodes if n["type"] == "employee"])
            st.metric("Employees", employee_count)
        
        with col2:
            system_count = len([n for n in filtered_nodes if n["type"] == "system"])
            st.metric("Systems", system_count)
        
        with col3:
            project_count = len([n for n in filtered_nodes if n["type"] == "project"])
            st.metric("Projects", project_count)
        
        with col4:
            st.metric("Connections", len(filtered_edges))
    
    finally:
        db.close()
