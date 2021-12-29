/******************************************
 *
 * CSS Nav Toggle
 *
 ******************************************/

// Finish this ...  clean up the code below with appropriate toggle functionality
const budgetOverview = document.querySelector(".budget-overview");
const budgetOverviewBtn = document.querySelector("#budget-overview-btn");

document
  .querySelector("#budget-overview-btn")
  .addEventListener("click", function () {
    document.querySelector(".budget-overview").style.display = "inline";
    document.querySelector("#budget-overview-btn").className =
      "nav-link active";
    document.querySelector(".budget-stats").style.display = "none";
    document.querySelector("#budget-stats-btn").className = "nav-link";
    document.querySelector(".budget-calc").style.display = "none";
    document.querySelector("#budget-calc-btn").className = "nav-link";
  });

document
  .querySelector("#budget-stats-btn")
  .addEventListener("click", function () {
    document.querySelector(".budget-overview").style.display = "none";
    document.querySelector("#budget-overview-btn").className = "nav-link";
    document.querySelector(".budget-stats").style.display = "inline";
    document.querySelector("#budget-stats-btn").className = "nav-link active";
    document.querySelector(".budget-calc").style.display = "none";
    document.querySelector("#budget-calc-btn").className = "nav-link";
  });

document
  .querySelector("#budget-calc-btn")
  .addEventListener("click", function () {
    document.querySelector(".budget-overview").style.display = "none";
    document.querySelector("#budget-overview-btn").className = "nav-link";
    document.querySelector(".budget-stats").style.display = "none";
    document.querySelector("#budget-stats-btn").className = "nav-link";
    document.querySelector(".budget-calc").style.display = "inline";
    document.querySelector("#budget-calc-btn").className = "nav-link active";
  });

/******************************************
 *
 * Budget Calculator
 *
 *****************************************/

// should define all the different elements that I want to select here
const containerBudgetLines = document.querySelector(".added_rows");
const containerBudget = document.querySelector(".budget");
const lineTotal = document.querySelector("#line_total");

// create budget object containg relevant variables
// this will be done using a Fetch API grabbing the data from the server
const budgetObj = {
  rates: [],
  code: [],
  hours: [],
  occurences: [],
  costService: [],
  totalCost: 0,
  budget: 0,
};

// declare ndis_code object, I want this available in the global scope
let ndis_codes = {};

// calculate budget
function budgetCalc(hrs, occur, code) {
  const hours = hrs;
  const occurences = occur;
  const cur_code = code;
  const cost =
    Math.round(hours * occurences * ndis_codes[11][cur_code] * 100) / 100;
  budgetObj.totalCost += cost;

  budgetObj.hours.push(hours);
  budgetObj.occurences.push(occurences);
  budgetObj.code.push(cur_code);
  budgetObj.rates.push(ndis_codes[11][cur_code]);
  budgetObj.costService.push(cost);
}

// update budget
function budgetUpdate() {
  budgetObj.budget;
  budgetObj.totalCost = 0;

  for (let i = 0; i < budgetObj.costService.length; i++) {
    budgetObj.costService[i] =
      Math.round(
        budgetObj.hours[i] * budgetObj.occurences[i] * budgetObj.rates[i] * 100
      ) / 100;
  }

  for (i = 0; i < budgetObj.costService.length; i++) {
    budgetObj.totalCost += budgetObj.costService[i];
  }
}

// render the budget lines
function renderBudgetLines(length) {
  containerBudgetLines.innerHTML = "";

  for (let i = 0; i < budgetObj.hours.length; i++) {
    listOfCodes = ndis_codes[1];

    const htmlComponents = [
      `<form class="row gy-2 gx-3 align-items-center">
                                    <div class="col-auto">
                                        <label class="visually-hidden" for="code">Code</label>
                                        <div class="input-group">
                                            <div class="input-group-text">Choose Code</div>
                                            <select class="form-control" name="code" id="code_${i}" onblur=updateExisitng(this)>`,
    ];

    Object.values(listOfCodes).forEach((code) => {
      if (code === budgetObj.code[i]) {
        htmlComponents.push(
          `<option value="${code}" selected="selected">${code}</option>`
        );
      } else {
        htmlComponents.push(`<option value="${code}">${code}</option>`);
      }
    });

    htmlComponents.push(`</select>
                                        </div>
                                    </div>
                                    <div class="col-auto">
                                        <label class="visually-hidden" for="hours">Hours</label>
                                        <div class="input-group">
                                            <div class="input-group-text">Hours</div>
                                            <input type="text" class="form-control" id="hours_${i}" onblur=updateExisitng(this) value="${budgetObj.hours[i]}">
                                        </div>
                                    </div>
                                    <div class="col-auto">
                                        <label class="visually-hidden" for="occurences">Occurences</label>
                                        <div class="input-group">
                                            <div class="input-group-text">Occurences</div>
                                            <input type="text" class="form-control" id="occurences_${i}" onblur=updateExisitng(this) value="${budgetObj.occurences[i]}">
                                        </div>
                                    </div>
                                    <div class="col-auto">
                                        <div class="input-group">
                                            <div class="input-group-text" id="linetotal_${i}" style="width: 8em;">$ ${budgetObj.costService[i]}</div>
                                        </div>
                                    </div>
                                    <div class="col-auto">
                                        <button type="button" class="btn btn-secondary btn-sm" id="update_${i}" onclick=updateLine(this)>Update</button>
                                    </div>
                                    <div class="col-auto">
                                        <button type="button" class="btn btn-secondary btn-sm" id="remove_${i}" onclick=removeLine(this)>X</button>
                                    </div>
                                </form>`);

    containerBudgetLines.insertAdjacentHTML(
      "afterbegin",
      htmlComponents.join()
    );
  }
}

// get input line fields from the top "add" line input
function getLineFields() {
  let lineFields = [];
  lineFields.push(document.querySelector("#code").value);
  lineFields.push(document.querySelector("#hours").value);
  lineFields.push(document.querySelector("#occurences").value);

  return lineFields;
}

// render the cost of service and budget lines
function renderBudget() {
  containerBudget.innerHTML = "";

  const color = budgetObj.budget - budgetObj.totalCost >= 0 ? "green" : "red";

  const htmlBudget = `<hr><p>Cost of New Services: $ ${
    Math.round(budgetObj.totalCost * 100) / 100
  }</p><p style="color: ${color};">Unallocated Budget: $ <span id="return_budget">${
    Math.round((budgetObj.budget - budgetObj.totalCost) * 100) / 100
  }</span></p>`;

  containerBudget.innerHTML = htmlBudget;
}

// remove lines (data at a specific index) from object and re-render the new lines
function removeLine(e) {
  let line_id = e.id;
  line_id = line_id.split("_");
  const r_id = parseInt(line_id[1]) + 1;

  // re-calculate totalCost
  budgetObj.totalCost -=
    Math.round(budgetObj.costService[line_id[1]] * 100) / 100;

  // remove element from hours, occurences, costService
  // hours
  const l_hrs = budgetObj.hours.slice(0, line_id[1]);
  const r_hrs = budgetObj.hours.slice(r_id);
  budgetObj.hours = l_hrs.concat(r_hrs);

  // occurences
  const l_occur = budgetObj.occurences.slice(0, line_id[1]);
  const r_occur = budgetObj.occurences.slice(r_id);
  budgetObj.occurences = l_occur.concat(r_occur);

  // costService
  const l_cost = budgetObj.costService.slice(0, line_id[1]);
  const r_cost = budgetObj.costService.slice(r_id);
  budgetObj.costService = l_cost.concat(r_cost);

  // re-render budget lines
  renderBudget();
  renderBudgetLines();
}

function updateExisitng(e) {
  let line_id = e.id;
  line_id = line_id.split("_");

  const newCode = document.querySelector(`#code_${line_id[1]}`).value;
  const newHrs = document.querySelector(`#hours_${line_id[1]}`).value;
  const newOcc = document.querySelector(`#occurences_${line_id[1]}`).value;

  if (
    newCode != budgetObj.code[line_id[1]] ||
    newHrs != budgetObj.hours[line_id[1]] ||
    newOcc != budgetObj.occurences[line_id[1]]
  ) {
    document.querySelector(`#update_${line_id[1]}`).style =
      "background-color: #198754";
  } else {
    document.querySelector(`#update_${line_id[1]}`).style =
      "background-color: #6c757d";
  }

  const total =
    Math.round(newHrs * newOcc * ndis_codes[11][newCode] * 100) / 100;

  updateExistingLineTotal(line_id[1], total);
}

function updateLine(e) {
  let line_id = e.id;
  line_id = line_id.split("_");
  const r_id = parseInt(line_id[1]) + 1;

  budgetObj.code[line_id[1]] = document.querySelector(
    `#code_${line_id[1]}`
  ).value;

  budgetObj.rates[line_id[1]] = ndis_codes[11][budgetObj.code[line_id[1]]];

  console.log(budgetObj);

  budgetObj.hours[line_id[1]] = document.querySelector(
    `#hours_${line_id[1]}`
  ).value;
  budgetObj.occurences[line_id[1]] = document.querySelector(
    `#occurences_${line_id[1]}`
  ).value;

  budgetUpdate();

  renderBudget();
  renderBudgetLines();
}

// update line total
function updateLineTotal(total) {
  lineTotal.innerHTML = `$ ${total}`;
}

function updateExistingLineTotal(i, total) {
  document.querySelector(`#linetotal_${i}`).innerHTML = `$ ${total}`;
}

// Add the initial budget
// this will be done using a Fetch API grabbing the data from the server
window.onload = function () {
  // Fetch Requset to API to get relevant NDIS codes
  fetch("/budget/ndis_codes", { method: "GET" }).then((response) => {
    response.json().then((data) => {
      ndis_codes = data;
    });
  });

  budgetObj.budget = parseFloat(
    document.querySelector("#return_budget").innerHTML
  );
  renderBudget();
  renderBudgetLines();
};

// listen for attempts at adding new lines
document.querySelector("#submit_add").addEventListener("click", function () {
  const hours = document.querySelector("#hours").value;
  const occurences = document.querySelector("#occurences").value;
  const selected_code = document.querySelector("#code").value;

  budgetCalc(hours, occurences, selected_code);

  renderBudget();
  renderBudgetLines();
});

// update the not-yet-added line total on 'blur'
document.querySelector("#code").addEventListener("blur", function () {
  const lineValues = getLineFields();

  const lineTotal =
    Math.round(
      lineValues[1] * lineValues[2] * ndis_codes[11][lineValues[0]] * 100
    ) / 100;

  updateLineTotal(lineTotal);
});

document.querySelector("#hours").addEventListener("blur", function () {
  const lineValues = getLineFields();

  const lineTotal =
    Math.round(
      lineValues[1] * lineValues[2] * ndis_codes[11][lineValues[0]] * 100
    ) / 100;

  updateLineTotal(lineTotal);
});

document.querySelector("#occurences").addEventListener("blur", function () {
  const lineValues = getLineFields();

  const lineTotal =
    Math.round(
      lineValues[1] * lineValues[2] * ndis_codes[11][lineValues[0]] * 100
    ) / 100;

  updateLineTotal(lineTotal);
});
