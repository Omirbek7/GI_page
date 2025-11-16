// Функция для обновления состояния игры
function updateGameState() {
    fetch('/game_state')
        .then(response => response.json())
        .then(data => {
            // Обновляем HP игрока и врага
            document.getElementById('player-hp').textContent = data.player_hp;
            document.getElementById('player-max-hp').textContent = data.player_max_hp;
            document.getElementById('player-dmg').textContent = data.player_dmg;
            document.getElementById('player-defense').textContent = data.player_defense;

            document.getElementById('enemy-hp').textContent = data.enemy_hp;
            document.getElementById('enemy-max-hp').textContent = data.enemy_max_hp;
            document.getElementById('enemy-dmg').textContent = data.enemy_dmg;
            document.getElementById('enemy-defense').textContent = data.enemy_defense;

            // Обновляем лог боя
            const battleLog = document.getElementById('battle-log');
            battleLog.innerHTML = ''; // Очищаем лог
            data.battle_log.forEach(log => {
                const logEntry = document.createElement('p');
                logEntry.textContent = log;
                battleLog.appendChild(logEntry);
            });

            // Показываем статус игры
            const status = document.getElementById('game-status');
            if (!data.game_running) {
                status.textContent = "Игра окончена";
                status.style.color = "red";
            } else {
                status.textContent = "Бой продолжается";
                status.style.color = "green";
            }
        })
        .catch(error => console.error('Ошибка:', error));

    // Повторяем запрос каждые 100 мс
    setTimeout(updateGameState, 100);
}

// Запускаем обновление и добавляем обработчик кнопки при загрузке страницы
window.onload = function() {
    updateGameState();
    document.getElementById('start-game').addEventListener('click', function() {
        fetch('/start/easy')  // Запускаем игру на легком уровне
            .then(response => response.json())
            .then(data => {
                console.log(data.status);  // "Game started"
            })
            .catch(error => console.error('Ошибка при старте игры:', error));
    });
};