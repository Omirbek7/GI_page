// script.js
document.querySelectorAll('.character-card').forEach(card => {
    card.addEventListener('click', () => {
        const characterName = card.dataset.name;
        alert(`You clicked on ${characterName}!`);
        // Здесь можно подгружать дополнительные данные
    });
});
