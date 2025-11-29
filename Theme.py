"""
Theme configuration for MIND Unified Dashboard
Colors: Light ash background, deep blue primary, red accents
"""

# Color Palette
COLORS = {
    'background': '#F5F5F5',        # Light ash background
    'primary': '#1B3B6F',           # Deep blue
    'secondary': '#2E5C8A',         # Medium blue
    'accent': '#DC143C',            # Crimson red
    'success': '#28A745',           # Green for positive metrics
    'warning': '#FFC107',           # Amber for warnings
    'danger': '#DC3545',            # Red for critical
    'text': '#2C3E50',              # Dark gray for text
    'text_light': '#6C757D',        # Light gray for secondary text
    'white': '#FFFFFF',
    'border': '#DEE2E6'
}

# Chart color schemes
CHART_COLORS = {
    'primary_gradient': ['#1B3B6F', '#2E5C8A', '#4A7BA7', '#6BA3C8'],
    'accent_gradient': ['#DC143C', '#E8385F', '#F25C7C', '#FF8099'],
    'mixed': ['#1B3B6F', '#DC143C', '#28A745', '#FFC107', '#2E5C8A'],
    'performance': ['#DC143C', '#FFC107', '#28A745'],  # Red -> Yellow -> Green
}

def get_plotly_theme():
    """Returns Plotly theme configuration"""
    return {
        'layout': {
            'paper_bgcolor': COLORS['white'],
            'plot_bgcolor': COLORS['background'],
            'font': {
                'family': 'Inter, sans-serif',
                'color': COLORS['text']
            },
            'title': {
                'font': {
                    'size': 18,
                    'color': COLORS['primary'],
                    'family': 'Inter, sans-serif'
                }
            },
            'xaxis': {
                'gridcolor': COLORS['border'],
                'linecolor': COLORS['border']
            },
            'yaxis': {
                'gridcolor': COLORS['border'],
                'linecolor': COLORS['border']
            },
            'colorway': CHART_COLORS['primary_gradient']
        }
    }

def apply_streamlit_theme():
    """Returns CSS for Streamlit custom theming"""
    return f"""
    <style>
        /* Main background */
        .stApp {{
            background-color: {COLORS['background']};
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {COLORS['white']};
            border-right: 2px solid {COLORS['border']};
        }}
        
        /* Headers */
        h1, h2, h3 {{
            color: {COLORS['primary']};
            font-family: 'Inter', sans-serif;
        }}
        
        /* Metric containers */
        [data-testid="stMetricValue"] {{
            color: {COLORS['primary']};
            font-size: 2rem;
            font-weight: 600;
        }}
        
        /* KPI cards */
        .kpi-card {{
            background-color: {COLORS['white']};
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid {COLORS['primary']};
        }}
        
        /* Accent elements */
        .accent-border {{
            border-left: 4px solid {COLORS['accent']};
        }}
        
        /* Buttons */
        .stButton>button {{
            background-color: {COLORS['primary']};
            color: {COLORS['white']};
            border-radius: 5px;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 500;
        }}
        
        .stButton>button:hover {{
            background-color: {COLORS['secondary']};
        }}
        
        /* Data tables */
        .dataframe {{
            border: 1px solid {COLORS['border']};
            border-radius: 5px;
        }}
        
        /* Info boxes */
        .stAlert {{
            background-color: {COLORS['white']};
            border-left: 4px solid {COLORS['primary']};
        }}
    </style>
    """
