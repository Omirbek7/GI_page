document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('damageCalculator');
    const result = document.getElementById('result');
    const critResult = document.getElementById('critResult');
    const elementalResult = document.getElementById('elementalResult');
    const elementalCritResult = document.getElementById('elementalCritResult');

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        // Получаем значения из формы
        const baseAtkChar = parseFloat(document.getElementById('baseAtkChar').value) || 0;
        const baseAtkWeapon = parseFloat(document.getElementById('baseAtkWeapon').value) || 0;
        const atkPercent = parseFloat(document.getElementById('atkPercent').value) / 100 || 0; // Переводим % в десятичную форму
        const flatAtk = parseFloat(document.getElementById('flatAtk').value) || 0;
        const critDmg = parseFloat(document.getElementById('critDmg').value) / 100 || 0; // Переводим % в десятичную форму
        const elementalBonus = parseFloat(document.getElementById('elementalBonus').value) / 100 || 0; // Переводим % в десятичную форму

        // Базовый урон (сумма ATK персонажа и оружия с бонусами)
        const totalAtk = (baseAtkChar + baseAtkWeapon) * (1 + atkPercent) + flatAtk;
        const baseDamage = totalAtk;

        // Общий урон
        result.textContent = `Общий урон: ${baseDamage.toFixed(2)}`;

        // Критический урон (с учётом Crit_DMG)
        const critDamage = baseDamage * (1 + critDmg);
        critResult.textContent = `Критический урон: ${critDamage.toFixed(2)}`;

        // Элементальный урон (с бонусом)
        const elementalDamage = baseDamage * (1 + elementalBonus);
        elementalResult.textContent = `Элементальный урон: ${elementalDamage.toFixed(2)}`;

        // Критический элементальный урон
        const elementalCritDamage = elementalDamage * (1 + critDmg);
        elementalCritResult.textContent = `Критический элементальный урон: ${elementalCritDamage.toFixed(2)}`;
    });
});
