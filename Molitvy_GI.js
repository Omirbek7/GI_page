document.addEventListener('DOMContentLoaded', () => {
    const banners = [
        'banner_arlechino.jpg',
        'banner_furina.webp',
        'banner_nahida.webp',
        'banner_navia.webp',
        'banner_neuvilette.jpg',
        'benner_shenhe.jpg', 
    ];
    
    // Функция для выбора случайного изображения
    function getRandomBanner() {
        return banners[Math.floor(Math.random() * banners.length)];
    }

    // Установка случайного фона для элемента #bannerImage
    document.getElementById('bannerImage').style.backgroundImage = `url(${getRandomBanner()})`;
});

// Функции для молитв
document.getElementById('pray').addEventListener('click', prayOnce);
document.getElementById('pray10').addEventListener('click', prayTenTimes);

function prayOnce() {
    performPray(1);
}

function prayTenTimes() {
    performPray(10);
}

function performPray(count) {
    let pity4 = parseInt(document.getElementById('pity4').textContent);
    let pity5 = parseInt(document.getElementById('pity5').textContent);
    let results = {3: 0, 4: 0, 5: 0};
    let chance5Star = 0.00601; // Начальный шанс

    for (let i = 0; i < count; i++) {
        if (pity5 > 74) {
            chance5Star = 0.00601 + (pity5 - 74) * 0.066266; 
        } else {
            chance5Star = 0.00601; // Возвращаем базовый шанс, если pity5 меньше 75
        }
        if (pity5 === 89) {
            chance5Star = 1; // 100% шанс на 90-й молитве
        }

        let random = Math.random();
        if (random < chance5Star) {
            results[5]++;
            pity4 = 0;
            pity5 = 0;
            chance5Star = 0.00601; // Сбрасываем шанс после получения 5★
        } else if (random < chance5Star + 0.051) { // шанс 4* фиксированный
            results[4]++;
            pity4 = 0;
            pity5++;
        } else {
            results[3]++;
            pity4++;
            pity5++;
        }

        // Убедимся, что после 9 молитв без 4*, 10-я молитва даст как минимум 4*
        if (pity4 === 10 && results[4] === 0 && results[5] === 0) {
// Повторяем 9-ю молитву с гарантированным 4* или 5*
            results[4]++; // Насильно добавляем 4*
            results[3]--;
            pity4 = 0; // Сбрасываем счетчик pity4
        }
    }

    // Формирование строки результата
    let resultStr = `Сделано ${count} молитв, результат:<br><div>`;
    for (let star of [5, 4, 3]) {
        if (results[star] > 0) {
            let colorClass = star === 5 ? 'star5' : (star === 4 ? 'star4' : '');
            resultStr += `<span class="${colorClass}">${star}★ (${results[star]} раз)</span>`;
        }
    }
    resultStr += `</div>`;

    // Вставка сформированного HTML в элемент с id 'result'
    document.getElementById('result').innerHTML = resultStr;
    document.getElementById('pity4').textContent = pity4;
    document.getElementById('pity5').textContent = pity5;
    
    // Отображение текущего шанса на 5★
    document.getElementById('chance5Star').textContent = `${(chance5Star * 100).toFixed(3)}%`;
}
