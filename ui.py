from flask import Flask, render_template_string

app = Flask(__name__)

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>Tracker Mockup</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body style="background: #f4f6f9;">

<nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
  <div class="container">
    <a class="navbar-brand fw-bold" href="/">ActiveTracker</a>
    <div class="d-flex">
        <a href="/exercises" class="btn btn-light fw-bold">Бібліотека вправ</a>
    </div>
  </div>
</nav>

<div class="container">
    <div class="row mb-4 text-center">
        <div class="col-md-4">
            <div class="card p-3 shadow-sm">
                <h3>1250</h3>
                <small>Тижневе навантаження</small>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card p-3 shadow-sm">
                <h3>178</h3>
                <small>Середнє / день</small>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card p-3 shadow-sm">
                <h3>5</h3>
                <small>Тренувань</small>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col-lg-8">
            <div class="card p-3 mb-4 shadow-sm">
                <canvas id="chart" height="100"></canvas>
            </div>
            
            <div class="card shadow-sm">
                <div class="card-header bg-white fw-bold">Останні тренування</div>
                <table class="table mb-0">
                    <tr>
                        <td>2023-10-25</td>
                        <td><span class="badge bg-secondary">run</span></td>
                        <td>45 хв</td>
                        <td>Load: <strong>216</strong></td>
                    </tr>
                    <tr>
                        <td>2023-10-24</td>
                        <td><span class="badge bg-secondary">gym</span></td>
                        <td>60 хв</td>
                        <td>Load: <strong>330</strong></td>
                    </tr>
                    <tr>
                        <td>2023-10-22</td>
                        <td><span class="badge bg-secondary">volleyball</span></td>
                        <td>90 хв</td>
                        <td>Load: <strong>450</strong></td>
                    </tr>
                </table>
            </div>
        </div>

        <div class="col-lg-4">
            <div class="card p-3 shadow-sm">
                <h5 class="mb-3">Додати запис</h5>
                <form>
                    <input type="date" class="form-control mb-2">
                    <select class="form-select mb-2">
                        <option>Біг</option>
                        <option>Зал</option>
                        <option>Волейбол</option>
                        <option>Інше</option>
                    </select>
                    <input type="number" class="form-control mb-2" placeholder="Хвилини">
                    <input type="number" class="form-control mb-2" placeholder="Інтенсивність (1-5)">
                    <button type="button" class="btn btn-primary w-100">Зберегти (Демо)</button>
                </form>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
    new Chart(document.getElementById('chart'), {
        type: 'line',
        data: {
            labels: ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд'],
            datasets: [{
                label: 'Приклад навантаження',
                data: [100, 250, 150, 300, 0, 400, 200],
                borderColor: '#0d6efd',
                tension: 0.3,
                fill: true
            }]
        }
    });
</script>
</body>
</html>
"""

HTML_LIBRARY = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>Бібліотека вправ (Макет)</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body style="background: #f4f6f9;">

<nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
  <div class="container">
    <a class="navbar-brand fw-bold" href="/">ActiveTracker</a>
    <div class="d-flex">
        <a href="/" class="btn btn-outline-light">На головну</a>
    </div>
  </div>
</nav>

<div class="container">
    <div class="text-center mb-5">
        <h1 class="fw-bold">Відео-бібліотека</h1>
        <p class="text-muted">Макет сторінки з прикладами карток</p>
    </div>

    <div class="mb-5">
        <h3 class="text-uppercase fw-bold border-bottom pb-2 mb-3 text-primary">Біг</h3>
        <div class="row row-cols-1 row-cols-md-3 g-4">
            
            <div class="col">
                <div class="card h-100 shadow-sm border-0">
                    <img src="https://ua.all.biz/img/ua/catalog/28253643.jpeg" class="card-img-top" style="height: 200px; object-fit: cover;">
                    <div class="card-body">
                        <h5 class="card-title fw-bold">Інтервальний біг</h5>
                        <p class="card-text text-muted">Приклад опису вправи...</p>
                    </div>
                    <div class="card-footer bg-white border-top-0">
                        <button class="btn btn-danger w-100">Дивитися відео</button>
                    </div>
                </div>
            </div>

            <div class="col">
                <div class="card h-100 shadow-sm border-0">
                    <img src="https://ua.all.biz/img/ua/catalog/28253643.jpeg" class="card-img-top" style="height: 200px; object-fit: cover;">
                    <div class="card-body">
                        <h5 class="card-title fw-bold">Біг під гору</h5>
                        <p class="card-text text-muted">Приклад опису вправи...</p>
                    </div>
                    <div class="card-footer bg-white border-top-0">
                        <button class="btn btn-danger w-100">Дивитися відео</button>
                    </div>
                </div>
            </div>

        </div>
    </div>

    <div class="mb-5">
        <h3 class="text-uppercase fw-bold border-bottom pb-2 mb-3 text-primary">Зал</h3>
        <div class="row row-cols-1 row-cols-md-3 g-4">
            
            <div class="col">
                <div class="card h-100 shadow-sm border-0">
                    <img src="https://ua.all.biz/img/ua/catalog/28253643.jpeg" class="card-img-top" style="height: 200px; object-fit: cover;">
                    <div class="card-body">
                        <h5 class="card-title fw-bold">Жим лежачи</h5>
                        <p class="card-text text-muted">Приклад опису вправи...</p>
                    </div>
                    <div class="card-footer bg-white border-top-0">
                        <button class="btn btn-danger w-100">Дивитися відео</button>
                    </div>
                </div>
            </div>

        </div>
    </div>
    
    <div class="text-center py-4">
        <a href="/" class="btn btn-secondary">Повернутися до трекера</a>
    </div>
</div>

</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(HTML_DASHBOARD)

@app.route("/exercises")
def exercises():
    return render_template_string(HTML_LIBRARY)

if __name__ == "__main__":
    app.run(debug=True)