document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.classList.add('shadow');
            setTimeout(() => btn.classList.remove('shadow'), 200);
        });
    });
});