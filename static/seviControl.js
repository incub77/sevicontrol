const {MDCSlider} = mdc.slider;
const {MDCRipple} = mdc.ripple;
const {MDCSwitch} = mdc.switchControl;
const {MDCFormField} = mdc.formField;
const {MDCRadio} = mdc.radio;
const {MDCDataTable} = mdc.dataTable;
const {MDCDialog} = mdc.dialog;
const {MDCTopAppBar} = mdc.topAppBar;

const reqURL = document.location.href.slice(0, -1);

const selector = '.mdc-button, .mdc-icon-button, .mdc-card__primary-action';
const ripples = [].map.call(document.querySelectorAll(selector),
    function (el) {
        return new MDCRipple(el);
    });

function CreateUUID() {
  return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
    (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
  )
}

// TopBar
const topAppBarElement = document.querySelector('.mdc-top-app-bar');
const topAppBar = new MDCTopAppBar(topAppBarElement);

const refreshButton = document.getElementById("button_refresh");
refreshButton.addEventListener("click", function() {
    document.location.reload();
});

// Update status box
function updateStatusBox() {
    fetch(`${reqURL}/status`)
        .then(res => res.json())
        .then((out) => {
            document.getElementById("mode_text").innerHTML = out["mode"];
            document.getElementById("power_text").innerHTML = out["power"];
            document.getElementById("level_text").innerHTML = out["level"];
        })
        .catch(error => console.error(error));
    fetch(`${reqURL}/getSleep`)
        .then(res => res.json())
        .then((out) => {
            document.getElementById("sleeping_text").innerHTML = out;
        })
        .catch(error => console.error(error));
    fetch(`${reqURL}/panelStatus`)
        .then(res => res.json())
        .then((out) => {
            document.getElementById("panel_text").innerHTML = out;
        })
        .catch(error => console.error(error));
}

updateStatusBox();
setInterval(updateStatusBox, 5000);

// create cron table
const dataTable = new MDCDataTable(document.querySelector(".mdc-data-table"));

function createCheckBoxTd(id) {
    let td = document.createElement("td");
    td.setAttribute("class", "mdc-data-table__cell mdc-data-table__cell--checkbox");
    let div = document.createElement("div");
    div.setAttribute("class", "mdc-checkbox mdc-data-table__row-checkbox");
    let input = document.createElement("input");
    input.setAttribute("type", "checkbox");
    input.setAttribute("class", "mdc-checkbox__native-control");
    input.setAttribute("aria-labelledby", id);
    let div2 = document.createElement("div");
    div2.setAttribute("class", "mdc-checkbox__background");
    // ugly hack... trying to create svg elements via createElementNS leads to false rendering...
    let hack = '<svg class="mdc-checkbox__checkmark" viewBox="0 0 24 24">\n';
    hack += '<path class="mdc-checkbox__checkmark-path" fill="none" d="M1.73,12.91 8.1,19.28 22.79,4.59"/>\n';
    hack += '</svg>\n<div class="mdc-checkbox__mixedmark"></div>';
    div2.innerHTML = hack;
    div.appendChild(input);
    div.appendChild(div2);
    td.appendChild(div);

    return td;
}

function createColumnsAndRows(tb, arr) {
    let _tr_ = document.createElement("tr");
    _tr_.setAttribute("class", "mdc-data-table__row");
    let _td_ = document.createElement("td");
    _td_.setAttribute("class", "mdc-data-table__cell");
    tb.innerHTML = "";
    for (let i = 0; i < arr.length; ++i) {
        let tr = _tr_.cloneNode(false);
        tr.setAttribute("data-row-id", arr[i]["id"]);
        tr.appendChild(createCheckBoxTd(arr[i]["id"]));
        let td = _td_.cloneNode(false);
        td.innerHTML = arr[i]["status"];
        tr.appendChild(td);
        let td1 = _td_.cloneNode(false);
        td1.innerHTML = arr[i]["days"];
        tr.appendChild(td1);
        let td2 = _td_.cloneNode(false);
        td2.innerHTML = `${arr[i]['hour']}:${arr[i]['minute']}`;
        tr.appendChild(td2);
        let td3 = _td_.cloneNode(false);
        td3.innerHTML = arr[i]["mode"];
        tr.appendChild(td3);
        tb.appendChild(tr);
    }
}

function updateCronTable() {
    fetch(`${reqURL}/cronData`)
        .then(res => res.json())
        .then((out) => {
            createColumnsAndRows(document.querySelector(".mdc-data-table__content"), out);
            dataTable.layout();
        })
        .catch(error => console.error(error));
}

updateCronTable();

// delete dialog
const deleteDialog = new MDCDialog(document.getElementById("cron-delete-dialog"));

const deleteButton = document.getElementById("cron_data_delete_button");
deleteButton.addEventListener("click", function () {
    let selRowsIds = dataTable.getSelectedRowIds();
    if (selRowsIds != "") {
        const dlg = document.getElementById("cron-delete-dialog-content");
        dlg.innerHTML = "IDs: <br>"+selRowsIds.join("<BR>");
        deleteDialog.open();
    }
});

deleteDialog.listen("MDCDialog:closed", function (ev) {
    if (ev.detail.action == "accept") {
        fetch(`${reqURL}/delCronData?ids=${dataTable.getSelectedRowIds()}`)
            .catch(error => console.error(error));
        updateCronTable();
    }
});


const addDialog = new MDCDialog(document.getElementById("cron-add-dialog"));
const addButton = document.getElementById("cron_data_add_button");
addButton.addEventListener("click", function() {
    addDialog.open();
    const cron_switchControl = new MDCSwitch(document.getElementById("cron-add-switch"));
    const cron_slider = new MDCSlider(document.getElementById("cron-add-slider"));
})


// update logs
//TODO: 2 rows... other format
function createLogRows(ul, arr) {
    let _li_ = document.createElement("li");
    _li_.setAttribute("class", "mdc-list-item");
    let _span_ = document.createElement("span");
    _span_.setAttribute("class", "mdc-list-item__text");
    let _span_primary_ = document.createElement("span");
    _span_primary_.setAttribute("class", "mdc-list-item__primary-text");
    let _span_secondary_ = document.createElement("span");
    _span_secondary_.setAttribute("class", "mdc-list-item__secondary-text");
    ul.innerHTML = "";
    for (let i = 0; i < arr.length; ++i) {
        let li = _li_.cloneNode(false);
        let span = _span_.cloneNode(false);
        let span1 = _span_primary_.cloneNode(false);
        span1.innerHTML = arr[i][0];
        let span2 = _span_secondary_.cloneNode(false);
        span2.innerHTML = arr[i][1];
        span.appendChild(span1);
        span.appendChild(span2);
        li.appendChild(span);
        ul.appendChild(li);
    }
}

function updateLogList() {
    fetch(`${reqURL}/logs`)
        .then(res => res.json())
        .then((out) => {
            createLogRows(document.querySelector(".mdc-list"), out);
        })
        .catch(error => console.error(error));
}

updateLogList();
setInterval(updateLogList, 5000);
