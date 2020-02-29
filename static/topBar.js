const MDCIconButtonToggle = mdc.iconButton.MDCIconButtonToggle;

const linkButton = document.getElementById("link-mode");
const iconToggle = new MDCIconButtonToggle(linkButton);


fetch(`${reqURL}/linkMode`)
        .then(res => res.json())
        .then((out) => {
            if( out["available"] === "false" ) {
                linkButton.setAttributeNode(document.createAttribute("disabled"));
            } else {
                if( out["active"] === "true" ) {
                    iconToggle.on = true;
                }
                else {
                    iconToggle.on = false;
                }
            }
        })
        .catch(error => console.error(error));


iconToggle.listen('MDCIconButtonToggle:change', function (event) {
    fetch(`${reqURL}/activateLink?${event.detail.isOn.toString()}`)
        .catch(error => console.error(error));
});

const refreshButton = document.getElementById("button_refresh");

refreshButton.addEventListener("click", function() {
    document.location.reload();
});