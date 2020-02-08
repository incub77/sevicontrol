
const switchControl = new MDCSwitch(document.getElementById("control-power-switch"));

const switchInput = document.getElementById("basic-switch");
switchInput.addEventListener('change', function () {
    if (switchInput.checked) {
        fetch(`${reqURL}/set?ON`)
            .catch(error => console.error(error));
    } else {
        fetch(`${reqURL}/set?OFF`)
            .catch(error => console.error(error));
    }
    updateStatusBox();
});

const radio = new MDCRadio(document.getElementById("control-mode-radio"));

const formField = new MDCFormField(document.getElementById("control-mode-form"));
formField.input = radio;
const radioInputs = document.querySelectorAll("[name=mode_radio]");
radioInputs[0].addEventListener('change', function () {
    fetch(`${reqURL}/setMode?W`)
        .catch(error => console.error(error));
    updateStatusBox();
});
radioInputs[1].addEventListener('change', function () {
    fetch(`${reqURL}/setMode?S`)
            .catch(error => console.error(error));
    updateStatusBox();
});


const slider = new MDCSlider(document.getElementById("control-level-slider"));

slider.listen('MDCSlider:change', function () {
    fetch(`${reqURL}/setLevel?${slider.value}`)
        .catch(error => console.error(error));
    updateStatusBox();
});


// Handle sleep buttons
const sleep1hButton = document.getElementById("sleep_1h_button");
sleep1hButton.addEventListener("click", function() {
    fetch(`${reqURL}/setSleep?duration=3600`)
            .catch(error => console.error(error));
    updateStatusBox();
});

const sleep2hButton = document.getElementById("sleep_2h_button");
sleep2hButton.addEventListener("click", function() {
    fetch(`${reqURL}/setSleep?duration=7200`)
            .catch(error => console.error(error));
    updateStatusBox();
});

const sleep4hButton = document.getElementById("sleep_4h_button");
sleep4hButton.addEventListener("click", function() {
    fetch(`${reqURL}/setSleep?duration=14400`)
            .catch(error => console.error(error));
    updateStatusBox();
});

//Initialize control card
function updateControlCard() {
    fetch(`${reqURL}/status`)
        .then((res) => {
            return res.json();
        })
        .then((out) => {
            if (out["power"] === "On") {
                document.querySelector(".mdc-switch").classList.add("mdc-switch--checked");
                document.querySelector(".mdc-switch__native-control").checked = true;
            } else {
                document.querySelector(".mdc-switch").classList.remove("mdc-switch--checked");
                document.querySelector(".mdc-switch__native-control").checked = false;
            }

            if (out["mode"] === "Rushing") {
                document.getElementById("switching").checked = false;
                document.getElementById("rushing").checked = true;
            } else {
                document.getElementById("switching").checked = true;
                document.getElementById("rushing").checked = false;
            }
            if (out["level"] !== '-') {
                slider.value = out["level"];
            }
        })
        .catch(error => console.error(error));
}
updateControlCard();
