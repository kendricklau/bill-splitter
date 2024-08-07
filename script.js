document.getElementById('upload-form').addEventListener('submit', function (e) {
  e.preventDefault();
  const formData = new FormData();
  const fileField = document.querySelector('input[type="file"]');

  formData.append('file', fileField.files[0]);

  console.log('Uploading file:', fileField.files[0]);

  fetch('https://bill-splitter-docker.onrender.com/upload', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    console.log('Upload response data:', data);
    const dishForm = document.getElementById('dish-form');
    const dishesDiv = document.getElementById('dishes');
    dishesDiv.innerHTML = '';
    dishForm.style.display = 'block';

    for (let dish in data.items) {
      const dishDiv = document.createElement('div');
      dishDiv.innerHTML = `<label>${dish} ($${data.items[dish]}):</label><br>`;
      const peopleInput = document.createElement('input');
      peopleInput.type = 'text';
      peopleInput.name = dish;
      peopleInput.placeholder = 'Comma separated names';
      dishDiv.appendChild(peopleInput);
      dishesDiv.appendChild(dishDiv);
    }

    document.getElementById('dish-form').addEventListener('submit', function (e) {
      e.preventDefault();

      const items = data.items;
      const tax = data.tax;
      const tip = data.tip;
      const payerName = document.getElementById('payer_name').value;
      const numPeople = document.getElementById('num_people').value;

      console.log('Form data:', { items, tax, tip, payerName, numPeople });

      const dishesPerPerson = {};
      const inputs = dishesDiv.getElementsByTagName('input');
      for (let input of inputs) {
        const dish = input.name;
        const people = input.value.split(',').map(p => p.trim());
        for (let person of people) {
          if (!dishesPerPerson[person]) {
            dishesPerPerson[person] = [];
          }
          dishesPerPerson[person].push(dish);
        }
      }

      console.log('Dishes per person:', dishesPerPerson);

      fetch('https://bill-splitter-docker.onrender.com/calculate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ items, tax, tip, payer_name: payerName, dishes_per_person: dishesPerPerson })
      })
      .then(response => response.json())
      .then(data => {
        console.log('Calculate response data:', data);
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = '<h2>Amounts Owed:</h2>';
        for (let person in data) {
          resultsDiv.innerHTML += `<p>${person}: $${data[person].toFixed(2)}</p>`;
        }
      });
    });
  })
  .catch(error => {
    console.error('Error:', error);
  });
});