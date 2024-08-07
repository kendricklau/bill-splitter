document.getElementById('initial-form').addEventListener('submit', function (e) {
  e.preventDefault();
  
  const payerName = document.getElementById('payer_name').value;
  const numPeople = document.getElementById('num_people').value;
  
  if (!payerName || !numPeople) {
    alert('Please enter the payer name and number of people.');
    return;
  }
  
  const peopleNamesDiv = document.getElementById('people-names');
  peopleNamesDiv.innerHTML = '';
  
  for (let i = 0; i < numPeople; i++) {
    const label = document.createElement('label');
    label.innerText = `Person ${i + 1} Name: `;
    const input = document.createElement('input');
    input.type = 'text';
    input.name = 'person_name';
    input.classList.add('person-name');
    input.setAttribute('data-index', i);
    input.required = true;
    peopleNamesDiv.appendChild(label);
    peopleNamesDiv.appendChild(input);
    peopleNamesDiv.appendChild(document.createElement('br'));
  }
  
  peopleNamesDiv.innerHTML += '<input type="button" value="Next" onclick="showUploadForm()">';
});

function showUploadForm() {
  const initialForm = document.getElementById('initial-form');
  const uploadForm = document.getElementById('upload-form');
  initialForm.style.display = 'none';
  uploadForm.style.display = 'block';
}

document.getElementById('upload-form').addEventListener('submit', function (e) {
  e.preventDefault();
  
  const formData = new FormData();
  const fileField = document.querySelector('input[type="file"]');
  formData.append('file', fileField.files[0]);
  
  fetch('https://bill-splitter-docker.onrender.com/upload', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    console.log('Upload response data:', data);
    
    const dishForm = document.getElementById('dish-form');
    const dishesDiv = document.getElementById('dishes');
    const personNames = Array.from(document.getElementsByClassName('person-name')).map(input => input.value);
    
    if (!dishForm || !dishesDiv) {
      console.error('Dish form or dishes div not found');
      return;
    }
    
    dishesDiv.innerHTML = '';
    dishForm.style.display = 'block';
    
    for (let dish in data.items) {
      const dishDiv = document.createElement('div');
      dishDiv.innerHTML = `<label>${dish} ($${data.items[dish]}):</label><br>`;
      
      personNames.forEach(person => {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.name = dish;
        checkbox.value = person;
        checkbox.id = `${dish}_${person}`;
        const checkboxLabel = document.createElement('label');
        checkboxLabel.htmlFor = `${dish}_${person}`;
        checkboxLabel.innerText = person;
        
        dishDiv.appendChild(checkbox);
        dishDiv.appendChild(checkboxLabel);
        dishDiv.appendChild(document.createElement('br'));
      });
      
      dishesDiv.appendChild(dishDiv);
    }
  })
  .catch(error => {
    console.error('Error:', error);
  });
});

document.getElementById('dish-form').addEventListener('submit', function (e) {
  e.preventDefault();
  
  const payerName = document.getElementById('payer_name').value;
  const dishesDiv = document.getElementById('dishes');
  const checkboxes = dishesDiv.getElementsByTagName('input');
  
  const items = {};
  const dishesPerPerson = {};
  
  for (let checkbox of checkboxes) {
    if (checkbox.checked) {
      const dish = checkbox.name;
      const person = checkbox.value;
      
      if (!items[dish]) {
        items[dish] = parseFloat(document.querySelector(`label[for="${dish}"]`).innerText.split('$')[1]);
      }
      
      if (!dishesPerPerson[person]) {
        dishesPerPerson[person] = [];
      }
      
      dishesPerPerson[person].push(dish);
    }
  }
  
  fetch('https://bill-splitter-docker.onrender.com/calculate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ items, payer_name: payerName, dishes_per_person: dishesPerPerson })
  })
  .then(response => response.json())
  .then(data => {
    console.log('Calculate response data:', data);
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<h2>Amounts Owed:</h2>';
    
    for (let person in data) {
      resultsDiv.innerHTML += `<p>${person}: $${data[person].total.toFixed(2)}</p>`;
      resultsDiv.innerHTML += '<ul>';
      data[person].dishes.forEach(dish => {
        resultsDiv.innerHTML += `<li>${dish.name}: $${dish.amount.toFixed(2)}</li>`;
      });
      resultsDiv.innerHTML += `<li>Tax: $${data[person].tax.toFixed(2)}</li>`;
      resultsDiv.innerHTML += `<li>Tip: $${data[person].tip.toFixed(2)}</li>`;
      resultsDiv.innerHTML += '</ul>';
    }
  });
});