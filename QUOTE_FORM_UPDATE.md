# Quote Management Modal Form Update

## Changes needed in quote_management.html

Replace the "New Quote Modal" section (lines 735-808) with this updated version:

```html
\u003c!-- New Quote Modal --\u003e
\u003cdiv class=\"modal-overlay\" id=\"newQuoteModal\"\u003e
    \u003cdiv class=\"modal\"\u003e
        \u003cdiv class=\"modal-header\"\u003e
            \u003cdiv\u003e
                \u003ch2 class=\"modal-title\"\u003eCreate New Quote\u003c/h2\u003e
                \u003cp class=\"modal-subtitle\"\u003eSearch catalog and create a quote for your client\u003c/p\u003e
            \u003c/div\u003e
            \u003cbutton type=\"button\" class=\"modal-close\" onclick=\"closeNewQuoteModal()\"\u003e×\u003c/button\u003e
        \u003c/div\u003e
        \u003cdiv class=\"modal-body\"\u003e
            \u003cform method=\"post\" id=\"newQuoteForm\" action=\"{% url 'create_multi_quote' %}\"\u003e
                {% csrf_token %}
                \u003c!-- Hidden fields for client/lead selection --\u003e
                \u003cinput type=\"hidden\" name=\"quote_type\" id=\"quote_type_input\"\u003e
                \u003cinput type=\"hidden\" name=\"client_id\" id=\"client_id_input\"\u003e
                \u003cinput type=\"hidden\" name=\"lead_id\" id=\"lead_id_input\"\u003e
                
                \u003cdiv class=\"form-row\"\u003e
                    \u003cdiv class=\"form-group\"\u003e
                        \u003clabel class=\"form-label\"\u003eClient/Lead Name *\u003c/label\u003e
                        \u003cselect class=\"form-input\" id=\"client_select\" required\u003e
                            \u003coption value=\"\"\u003eSelect client or lead...\u003c/option\u003e
                            \u003coptgroup label=\"Active Clients\"\u003e
                                {% for client in clients %}
                                \u003coption value=\"client_{{ client.id }}\"\u003e{{ client.name }} (Client)\u003c/option\u003e
                                {% endfor %}
                            \u003c/optgroup\u003e
                            \u003coptgroup label=\"Active Leads\"\u003e
                                {% for lead in leads %}
                                \u003coption value=\"lead_{{ lead.id }}\"\u003e{{ lead.name }} (Lead)\u003c/option\u003e
                                {% endfor %}
                            \u003c/optgroup\u003e
                        \u003c/select\u003e
                    \u003c/div\u003e
                    \u003cdiv class=\"form-group\"\u003e
                        \u003clabel class=\"form-label\"\u003eAccount Manager\u003c/label\u003e
                        \u003cinput type=\"text\" class=\"form-input\" value=\"{{ request.user.get_full_name }}\" readonly style=\"background-color: #f3f4f6;\"\u003e
                        \u003cinput type=\"hidden\" name=\"account_manager\" value=\"{{ request.user.id }}\"\u003e
                    \u003c/div\u003e
                \u003c/div\u003e
                
                \u003cdiv class=\"form-group\"\u003e
                    \u003clabel class=\"form-label\"\u003eProduct *\u003c/label\u003e
                    \u003cselect class=\"form-select\" name=\"product\" id=\"product_select\" required\u003e
                        \u003coption value=\"\"\u003eSelect a product...\u003c/option\u003e
                        {% for product in products %}
                        \u003coption value=\"{{ product.id }}\" data-name=\"{{ product.name }}\" data-sku=\"{{ product.sku }}\" data-type=\"{{ product.product_type }}\" data-price=\"{{ product.base_price }}\"\u003e
                            {{ product.name }} ({{ product.sku }}) - KES {{ product.base_price|floatformat:2 }}
                        \u003c/option\u003e
                        {% endfor %}
                    \u003c/select\u003e
                \u003c/div\u003e
                
                \u003cdiv class=\"form-row\"\u003e
                    \u003cdiv class=\"form-group\"\u003e
                        \u003clabel class=\"form-label\"\u003eQuantity *\u003c/label\u003e
                        \u003cinput type=\"number\" class=\"form-input\" name=\"quantity\" value=\"100\" min=\"1\" required\u003e
                    \u003c/div\u003e
                    \u003cdiv class=\"form-group\"\u003e
                        \u003clabel class=\"form-label\"\u003eUnit Price (KES) *\u003c/label\u003e
                        \u003cinput type=\"number\" class=\"form-input\" name=\"unit_price\" id=\"unit_price_input\" step=\"0.01\" min=\"0\" required\u003e
                    \u003c/div\u003e
                \u003c/div\u003e
                
                \u003cdiv class=\"form-group\"\u003e
                    \u003clabel class=\"form-label\"\u003eNotes\u003c/label\u003e
                    \u003ctextarea class=\"form-textarea\" name=\"notes\" placeholder=\"Add any special requirements or notes...\"\u003e\u003c/textarea\u003e
                \u003c/div\u003e
                
                \u003cdiv class=\"modal-footer\"\u003e
                    \u003cbutton type=\"button\" class=\"btn btn-secondary\" onclick=\"closeNewQuoteModal()\"\u003eCancel\u003c/button\u003e
                    \u003cbutton type=\"submit\" class=\"btn btn-primary\"\u003eCreate Quote\u003c/button\u003e
                \u003c/div\u003e
            \u003c/form\u003e
        \u003c/div\u003e
    \u003c/div\u003e
\u003c/div\u003e
```

## JavaScript Updates

Replace the JavaScript at the bottom (around line 929-996) with:

```javascript
// Client/Lead selection handler
document.getElementById('client_select').addEventListener('change', function() {
    const selectedValue = this.value;
    const quoteTypeInput = document.getElementById('quote_type_input');
    const clientIdInput = document.getElementById('client_id_input');
    const leadIdInput = document.getElementById('lead_id_input');
    
    if (selectedValue.startsWith('client_')) {
        quoteTypeInput.value = 'client';
        clientIdInput.value = selectedValue.replace('client_', '');
        leadIdInput.value = '';
    } else if (selectedValue.startsWith('lead_')) {
        quoteTypeInput.value = 'lead';
        leadIdInput.value = selectedValue.replace('lead_', '');
        clientIdInput.value = '';
    }
});

// Auto-fill product price when product is selected
document.getElementById('product_select').addEventListener('change', function() {
    const selectedOption = this.options[this.selectedIndex];
    const price = selectedOption.getAttribute('data-price');
    
    if (price) {
        document.getElementById('unit_price_input').value = price;
    }
});
```

## Key Changes:

1. **Account Manager Field**: Added readonly field showing logged-in user's name
2. **Client/Lead Dropdown**: Properly populated with registered clients and leads
3. **Product Dropdown**: Shows products from database with auto-fill price
4. **Form Action**: Points to `create_multi_quote` URL
5. **Hidden Fields**: Properly set client_id/lead_id based on selection
6. **JavaScript**: Handles client/lead selection and price auto-fill

The form now:
- Shows dropdown of clients and leads ✓
- Auto-fills account manager name ✓
- Shows products from production team's catalog ✓
- Auto-fills unit price when product selected ✓
- Submits data to backend properly ✓
