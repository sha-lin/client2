"""
Script to generate all admin list templates
"""

templates = {
    'clients_list.html': {
        'title': 'Clients',
        'model': 'client',
        'fields': ['client_id', 'name', 'email', 'phone', 'status', 'created_at'],
        'filters': ['status'],
    },
    'leads_list.html': {
        'title': 'Leads',
        'model': 'lead',
        'fields': ['lead_id', 'name', 'email', 'status', 'source', 'created_at'],
        'filters': ['status', 'source'],
    },
    'quotes_list.html': {
        'title': 'Quotes',
        'model': 'quote',
        'fields': ['quote_id', 'product_name', 'client', 'quantity', 'total_amount', 'status', 'quote_date'],
        'filters': ['status'],
    },
    'products_list.html': {
        'title': 'Products',
        'model': 'product',
        'fields': ['product_id', 'name', 'description', 'price', 'created_at'],
        'filters': [],
    },
    'jobs_list.html': {
        'title': 'Jobs',
        'model': 'job',
        'fields': ['job_number', 'quote', 'job_status', 'created_at'],
        'filters': ['job_status'],
    },
    'vendors_list.html': {
        'title': 'Vendors',
        'model': 'vendor',
        'fields': ['vendor_name', 'email', 'phone', 'is_active', 'created_at'],
        'filters': ['is_active'],
    },
    'processes_list.html': {
        'title': 'Processes',
        'model': 'process',
        'fields': ['process_name', 'description', 'created_at'],
        'filters': [],
    },
    'qc_list.html': {
        'title': 'Quality Control',
        'model': 'qc',
        'fields': ['job', 'status', 'progress', 'created_at'],
        'filters': ['status'],
    },
    'deliveries_list.html': {
        'title': 'Deliveries',
        'model': 'delivery',
        'fields': ['job', 'status', 'created_at'],
        'filters': ['status'],
    },
    'lpos_list.html': {
        'title': 'LPOs',
        'model': 'lpo',
        'fields': ['lpo_number', 'vendor', 'status', 'created_at'],
        'filters': ['status'],
    },
    'payments_list.html': {
        'title': 'Payments',
        'model': 'payment',
        'fields': ['payment_id', 'invoice_number', 'payment_status', 'amount', 'created_at'],
        'filters': ['payment_status'],
    },
    'users_list.html': {
        'title': 'Users',
        'model': 'user',
        'fields': ['username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined'],
        'filters': ['is_active'],
    },
}

def generate_template(name, config):
    """Generate a list template"""
    title = config['title']
    model = config['model']
    
    template = f"""{% extends 'admin/includes/list_base.html' %}
{% load humanize %}

{generate_filters(config['filters'], model)}

{% block table_header %}
    <tr>
        {generate_headers(config['fields'], title)}
        <th>Actions</th>
    </tr>
{% endblock %}

{% block table_body %}
    {{% for item in page_obj %}}
        <tr>
            {generate_cells(config['fields'], model)}
            <td>
                <div class="row-actions">
                    <button class="action-btn" onclick="openEditModal({{{{ item.id }}}})">✎ Edit</button>
                    <button class="action-btn danger" onclick="deleteItem({{{{ item.id }}}})">🗑 Delete</button>
                </div>
            </td>
        </tr>
    {{% endfor %}}
{% endblock %}

{% block extra_js %}
<script>
    function openCreateModal() {{
        alert('Create modal not yet implemented');
    }}
    
    function openEditModal(id) {{
        alert('Edit modal not yet implemented');
    }}
    
    function deleteItem(id) {{
        if (confirm('Are you sure?')) {{
            alert('Delete not yet implemented');
        }}
    }}
</script>
{% endblock %}"""
    
    return template

def generate_filters(filters, model):
    """Generate filter controls"""
    if not filters:
        return ""
    
    html = "{% block filter_controls %}\n"
    for f in filters:
        html += f'    <select name="{f}" class="filter-select" onchange="this.form.submit()">\n'
        html += f'        <option value="">All {f.title()}</option>\n'
        html += f'    </select>\n'
    html += "{% endblock %}"
    return html

def generate_headers(fields, title):
    """Generate table headers"""
    headers = []
    for field in fields:
        headers.append(f"<th>{field.replace('_', ' ').title()}</th>")
    return "\n        ".join(headers)

def generate_cells(fields, model):
    """Generate table cells"""
    cells = []
    for field in fields:
        cells.append(f'<td>{{{{ item.{field} }}}}</td>')
    return "\n            ".join(cells)

# Generate all templates
for filename, config in templates.items():
    content = generate_template(filename, config)
    path = f"c:\\Users\\Administrator\\Desktop\\client\\clientapp\\templates\\admin\\{filename}"
    print(f"Would generate: {path}")
    print(f"Content preview:\n{content[:200]}...\n")

print("Template generation complete!")
