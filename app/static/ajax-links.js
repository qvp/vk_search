function initAjaxLinks() {
    document.addEventListener('click', function (e) {
        const link = e.target.closest('a[data-ajax]');
        if (!link) return;

        // Защита от повторного клика
        if (link.dataset.loading === 'true') {
            e.preventDefault();
            return;
        }

        e.preventDefault();

        const parent = link.parentElement;
        if (!parent) return;

        const originalText = link.textContent;

        // Блокируем повторный клик и меняем текст
        link.dataset.loading = 'true';
        link.textContent = 'Проверяем...';
        link.style.pointerEvents = 'none';

        fetch(link.href, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            redirect: 'follow',
            credentials: 'same-origin'
        })
            .then(function (response) {
                // Если сервер сделал редирект — response.redirected === true
                if (response.redirected) {
                    window.location.href = response.url;
                    return null;
                }
                return response.text();
            })
            .then(function (html) {
                if (html === null) return; // был редирект

                parent.innerHTML = html;
            })
            .catch(function (err) {
                console.error('AJAX error:', err);
                // Возвращаем ссылку в исходное состояние при ошибке
                link.textContent = originalText;
                link.dataset.loading = 'false';
                link.style.pointerEvents = '';
            });
    });
}

// Инициализация
initAjaxLinks();
