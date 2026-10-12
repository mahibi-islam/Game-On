// Attach the CSRF token (from <meta name="csrf-token">) to every same-origin
// POST: as an X-CSRFToken header on fetch() calls and as a hidden field on forms.
(function () {
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (!meta) return;
    var token = meta.getAttribute('content');

    var originalFetch = window.fetch;
    window.fetch = function (input, init) {
        init = init || {};
        var method = (init.method || (input && input.method) || 'GET').toUpperCase();
        var url = new URL(typeof input === 'string' ? input : input.url, window.location.href);
        if (method !== 'GET' && method !== 'HEAD' && url.origin === window.location.origin) {
            var headers = new Headers(init.headers || (typeof input === 'string' ? undefined : input.headers));
            headers.set('X-CSRFToken', token);
            init.headers = headers;
        }
        return originalFetch.call(this, input, init);
    };

    function addTokenField(form) {
        if ((form.getAttribute('method') || '').toUpperCase() !== 'POST') return;
        if (form.querySelector('input[name="csrf_token"]')) return;
        var field = document.createElement('input');
        field.type = 'hidden';
        field.name = 'csrf_token';
        field.value = token;
        form.appendChild(field);
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('form').forEach(addTokenField);
    });
    // Covers forms added or changed after page load
    document.addEventListener('submit', function (e) { addTokenField(e.target); }, true);
})();
