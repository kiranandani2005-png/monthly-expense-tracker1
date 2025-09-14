// Script for Graphs Page

async function updateGraph() {
    const graphType = document.getElementById('graphType').value;
    const timeFrame = document.getElementById('timeFrame').value;

    const response = await fetch('/get_transactions');
    const transactions = await response.json();

    // Process transactions based on time frame
    const labels = [];
    const incomeData = [];
    const expenseData = [];

    const now = new Date();
    const oneDay = 24 * 60 * 60 * 1000;

    if (timeFrame === 'daily') {
        const days = 7; // last 7 days
        for (let i = days - 1; i >= 0; i--) {
            const day = new Date(now - i * oneDay);
            const label = day.toISOString().split('T')[0];
            labels.push(label);
            let incomeSum = 0;
            let expenseSum = 0;
            transactions.forEach(t => {
                if (t.date === label) {
                    if (t.type === 'income') incomeSum += t.amount;
                    if (t.type === 'expense') expenseSum += t.amount;
                }
            });
            incomeData.push(incomeSum);
            expenseData.push(expenseSum);
        }
    } else if (timeFrame === 'weekly') {
        for (let i = 4; i >= 1; i--) {
            const start = new Date(now - i * 7 * oneDay);
            const end = new Date(start.getTime() + 6 * oneDay);
            const label = `${start.toISOString().split('T')[0]} - ${end.toISOString().split('T')[0]}`;
            labels.push(label);
            let incomeSum = 0;
            let expenseSum = 0;
            transactions.forEach(t => {
                const tDate = new Date(t.date);
                if (tDate >= start && tDate <= end) {
                    if (t.type === 'income') incomeSum += t.amount;
                    if (t.type === 'expense') expenseSum += t.amount;
                }
            });
            incomeData.push(incomeSum);
            expenseData.push(expenseSum);
        }
    } else if (timeFrame === 'monthly') {
        const months = ["January","February","March","April","May","June","July","August","September","October","November","December"];
        for (let i = 0; i < 12; i++) {
            labels.push(months[i]);
            let incomeSum = 0;
            let expenseSum = 0;
            transactions.forEach(t => {
                const tDate = new Date(t.date);
                if (tDate.getMonth() === i) {
                    if (t.type === 'income') incomeSum += t.amount;
                    if (t.type === 'expense') expenseSum += t.amount;
                }
            });
            incomeData.push(incomeSum);
            expenseData.push(expenseSum);
        }
    } else if (timeFrame === 'yearly') {
        const currentYear = now.getFullYear();
        for (let y = currentYear - 4; y <= currentYear; y++) {
            labels.push(y.toString());
            let incomeSum = 0;
            let expenseSum = 0;
            transactions.forEach(t => {
                const tDate = new Date(t.date);
                if (tDate.getFullYear() === y) {
                    if (t.type === 'income') incomeSum += t.amount;
                    if (t.type === 'expense') expenseSum += t.amount;
                }
            });
            incomeData.push(incomeSum);
            expenseData.push(expenseSum);
        }
    }

    // Destroy previous chart if exists
    if (window.myChart) window.myChart.destroy();

    const ctx = document.getElementById('chartCanvas').getContext('2d');
    window.myChart = new Chart(ctx, {
        type: graphType,
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Income',
                    data: incomeData,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1,
                    fill: graphType !== 'line'
                },
                {
                    label: 'Expense',
                    data: expenseData,
                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1,
                    fill: graphType !== 'line'
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Profit / Loss Comparison
    const comp = await fetch('/compare');
    const compData = await comp.json();
    const statusText = `This Month: ₹${compData.this_month_total}, Last Month: ₹${compData.last_month_total}, ${compData.status}: ₹${Math.abs(compData.difference)}`;
    document.getElementById('status').innerText = statusText;
}

