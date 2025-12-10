"""
Generate clean Django admin-style list templates for all admin models
Run this script to regenerate corrupted or missing templates
"""

TEMPLATES = {
    'vendors_list.html': '''{% extends 'admin/generic_list.html' %}
{% load humanize %}

{% block filter_controls %}
    <select name="status" onchange="this.form.submit()" style="padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px;">
        <option value="">All Status</option>
        <option value="active">Active</option>
        <option value="inactive">Inactive</option>
    </select>
{% endblock %}

{% block table_header %}
    <tr>
        <th>Vendor ID</th>
        <th>Name</th>
        <th>Email</th>
        <th>Phone</th>
        <th>Status</th>
        <th>Created</th>
        <th>Actions</th>
    </tr>
{% endblock %}

{% block table_body %}
    {% for vendor in page_obj %}
        <tr>
            <td><a href="{% url 'admin_vendor_detail' vendor.pk %}" style="color: #3b82f6;">{{ vendor.vendor_id }}</a></td>
            <td>{{ vendor.name }}</td>
            <td>{{ vendor.email }}</td>
            <td>{{ vendor.phone }}</td>
            <td><span class="badge badge-success">{{ vendor.status }}</span></td>
            <td>{{ vendor.created_at|date:"M d, Y" }}</td>
            <td><a href="{% url 'admin_vendor_detail' vendor.pk %}" class="action-btn">Edit</a> | <a href="{% url 'admin_vendor_delete' vendor.pk %}" class="action-btn danger">Delete</a></td>
        </tr>
    {% endfor %}
{% endblock %}
''',

    'processes_list.html': '''{% extends 'admin/generic_list.html' %}
{% load humanize %}

{% block table_header %}
    <tr>
        <th>Process Code</th>
        <th>Name</th>
        <th>Description</th>
        <th>Created</th>
        <th>Actions</th>
    </tr>
{% endblock %}

{% block table_body %}
    {% for process in page_obj %}
        <tr>
            <td><a href="{% url 'admin_process_detail' process.pk %}" style="color: #3b82f6;">{{ process.process_code }}</a></td>
            <td>{{ process.process_name }}</td>
            <td>{{ process.description|truncatewords:10 }}</td>
            <td>{{ process.created_at|date:"M d, Y" }}</td>
            <td><a href="{% url 'admin_process_detail' process.pk %}" class="action-btn">Edit</a> | <a href="{% url 'admin_process_delete' process.pk %}" class="action-btn danger">Delete</a></td>
        </tr>
    {% endfor %}
{% endblock %}
''',

    'lpos_list.html': '''{% extends 'admin/generic_list.html' %}
{% load humanize %}

{% block filter_controls %}
    <select name="status" onchange="this.form.submit()" style="padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px;">
        <option value="">All Status</option>
        <option value="pending">Pending</option>
        <option value="approved">Approved</option>
        <option value="completed">Completed</option>
    </select>
{% endblock %}

{% block table_header %}
    <tr>
        <th>LPO Number</th>
        <th>Client</th>
        <th>Amount</th>
        <th>Status</th>
        <th>Created</th>
        <th>Actions</th>
    </tr>
{% endblock %}

{% block table_body %}
    {% for lpo in page_obj %}
        <tr>
            <td><a href="{% url 'admin_lpo_detail' lpo.pk %}" style="color: #3b82f6;">{{ lpo.lpo_number }}</a></td>
            <td>{{ lpo.client.name }}</td>
            <td>{{ lpo.total_amount|floatformat:2 }}</td>
            <td><span class="badge badge-warning">{{ lpo.status }}</span></td>
            <td>{{ lpo.created_at|date:"M d, Y" }}</td>
            <td><a href="{% url 'admin_lpo_detail' lpo.pk %}" class="action-btn">Edit</a> | <a href="{% url 'admin_lpo_delete' lpo.pk %}" class="action-btn danger">Delete</a></td>
        </tr>
    {% endfor %}
{% endblock %}
''',

    'payments_list.html': '''{% extends 'admin/generic_list.html' %}
{% load humanize %}

{% block filter_controls %}
    <select name="status" onchange="this.form.submit()" style="padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px;">
        <option value="">All Status</option>
        <option value="pending">Pending</option>
        <option value="completed">Completed</option>
    </select>
{% endblock %}

{% block table_header %}
    <tr>
        <th>Payment ID</th>
        <th>Client</th>
        <th>Amount</th>
        <th>Method</th>
        <th>Status</th>
        <th>Date</th>
        <th>Actions</th>
    </tr>
{% endblock %}

{% block table_body %}
    {% for payment in page_obj %}
        <tr>
            <td><a href="{% url 'admin_payment_detail' payment.pk %}" style="color: #3b82f6;">{{ payment.payment_id }}</a></td>
            <td>{{ payment.client.name }}</td>
            <td>{{ payment.amount|floatformat:2 }}</td>
            <td>{{ payment.payment_method }}</td>
            <td><span class="badge badge-success">{{ payment.status }}</span></td>
            <td>{{ payment.payment_date|date:"M d, Y" }}</td>
            <td><a href="{% url 'admin_payment_detail' payment.pk %}" class="action-btn">Edit</a> | <a href="{% url 'admin_payment_delete' payment.pk %}" class="action-btn danger">Delete</a></td>
        </tr>
    {% endfor %}
{% endblock %}
''',

    'users_list.html': '''{% extends 'admin/generic_list.html' %}
{% load humanize %}

{% block filter_controls %}
    <select name="is_staff" onchange="this.form.submit()" style="padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px;">
        <option value="">All Users</option>
        <option value="true">Staff Only</option>
        <option value="false">Regular Only</option>
    </select>
{% endblock %}

{% block table_header %}
    <tr>
        <th>Username</th>
        <th>Email</th>
        <th>Full Name</th>
        <th>Staff</th>
        <th>Joined</th>
        <th>Actions</th>
    </tr>
{% endblock %}

{% block table_body %}
    {% for user in page_obj %}
        <tr>
            <td><a href="{% url 'admin_user_detail' user.pk %}" style="color: #3b82f6;">{{ user.username }}</a></td>
            <td>{{ user.email }}</td>
            <td>{{ user.get_full_name|default:'-' }}</td>
            <td><span class="badge {% if user.is_staff %}badge-success{% else %}badge-warning{% endif %}">{% if user.is_staff %}Yes{% else %}No{% endif %}</span></td>
            <td>{{ user.date_joined|date:"M d, Y" }}</td>
            <td><a href="{% url 'admin_user_detail' user.pk %}" class="action-btn">Edit</a> | <a href="{% url 'admin_user_delete' user.pk %}" class="action-btn danger">Delete</a></td>
        </tr>
    {% endfor %}
{% endblock %}
''',

    'qc_list.html': '''{% extends 'admin/generic_list.html' %}
{% load humanize %}

{% block filter_controls %}
    <select name="status" onchange="this.form.submit()" style="padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px;">
        <option value="">All Status</option>
        <option value="passed">Passed</option>
        <option value="failed">Failed</option>
        <option value="pending">Pending</option>
    </select>
{% endblock %}

{% block table_header %}
    <tr>
        <th>QC ID</th>
        <th>Job</th>
        <th>Status</th>
        <th>Inspected By</th>
        <th>Date</th>
        <th>Actions</th>
    </tr>
{% endblock %}

{% block table_body %}
    {% for qc in page_obj %}
        <tr>
            <td><a href="#" style="color: #3b82f6;">#{{ qc.id }}</a></td>
            <td>{{ qc.job.job_number }}</td>
            <td><span class="badge {% if qc.status == 'passed' %}badge-success{% else %}badge-danger{% endif %}">{{ qc.status }}</span></td>
            <td>{{ qc.inspected_by.get_full_name|default:'-' }}</td>
            <td>{{ qc.inspection_date|date:"M d, Y" }}</td>
            <td><a href="#" class="action-btn">View</a></td>
        </tr>
    {% endfor %}
{% endblock %}
''',

    'deliveries_list.html': '''{% extends 'admin/generic_list.html' %}
{% load humanize %}

{% block filter_controls %}
    <select name="status" onchange="this.form.submit()" style="padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px;">
        <option value="">All Status</option>
        <option value="pending">Pending</option>
        <option value="delivered">Delivered</option>
        <option value="failed">Failed</option>
    </select>
{% endblock %}

{% block table_header %}
    <tr>
        <th>Delivery ID</th>
        <th>Job</th>
        <th>Client</th>
        <th>Status</th>
        <th>Date</th>
        <th>Actions</th>
    </tr>
{% endblock %}

{% block table_body %}
    {% for delivery in page_obj %}
        <tr>
            <td><a href="#" style="color: #3b82f6;">#{{ delivery.id }}</a></td>
            <td>{{ delivery.job.job_number }}</td>
            <td>{{ delivery.job.quote.client.name }}</td>
            <td><span class="badge badge-info">{{ delivery.status }}</span></td>
            <td>{{ delivery.delivery_date|date:"M d, Y"|default:'-' }}</td>
            <td><a href="#" class="action-btn">View</a></td>
        </tr>
    {% endfor %}
{% endblock %}
''',

    'alerts_list.html': '''{% extends 'admin/generic_list.html' %}
{% load humanize %}

{% block filter_controls %}
    <select name="severity" onchange="this.form.submit()" style="padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px;">
        <option value="">All Severity</option>
        <option value="error">Error</option>
        <option value="warning">Warning</option>
        <option value="info">Info</option>
    </select>
{% endblock %}

{% block table_header %}
    <tr>
        <th>Alert ID</th>
        <th>Title</th>
        <th>Message</th>
        <th>Severity</th>
        <th>Created</th>
        <th>Actions</th>
    </tr>
{% endblock %}

{% block table_body %}
    {% for alert in page_obj %}
        <tr>
            <td>#{{ alert.id }}</td>
            <td>{{ alert.title }}</td>
            <td>{{ alert.message|truncatewords:10 }}</td>
            <td><span class="badge {% if alert.severity == 'error' %}badge-danger{% elif alert.severity == 'warning' %}badge-warning{% else %}badge-info{% endif %}">{{ alert.severity }}</span></td>
            <td>{{ alert.created_at|date:"M d, Y" }}</td>
            <td><a href="#" class="action-btn">Dismiss</a></td>
        </tr>
    {% endfor %}
{% endblock %}
''',
}

# Write each template
import os
template_dir = 'clientapp/templates/admin'

for filename, content in TEMPLATES.items():
    filepath = os.path.join(template_dir, filename)
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Created/Updated: {filepath}")

print("\nAll templates created successfully!")
