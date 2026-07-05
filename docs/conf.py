project = "fincore-py"
author = "fincore contributors"
copyright = "2026, fincore contributors"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]
templates_path = ["_templates"]
exclude_patterns = []
html_theme = "furo"
html_logo = "_static/fincore-wordmark.svg"
html_static_path = ["_static"]
html_css_files = ["brand.css"]
html_title = "fincore-py"
html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#7A1E1E",
        "color-brand-content": "#7A1E1E",
        "color-api-name": "#9A3A3A",
        "color-background-primary": "#101010",
        "color-background-secondary": "#171717",
        "color-foreground-primary": "#E7E0D0",
        "color-foreground-secondary": "#A8A299",
    },
    "dark_css_variables": {
        "color-brand-primary": "#7A1E1E",
        "color-brand-content": "#7A1E1E",
        "color-api-name": "#9A3A3A",
        "color-background-primary": "#0A0A0A",
        "color-background-secondary": "#171717",
        "color-foreground-primary": "#E7E0D0",
        "color-foreground-secondary": "#A8A299",
    },
    "source_repository": "https://github.com/avi2413/fincore/",
    "source_branch": "main",
    "source_directory": "docs/",
}
autodoc_typehints = "description"
