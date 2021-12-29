function getId(str) {
    let result = [];
    let passed_id = str;
    for (let i = passed_id.length-1; i > -1; i--) {
        if ( passed_id[i] === "-") {
            return result.reverse().join("");;
        } else {
            result.push(passed_id[i]);
        }
    }
    return `${passed_id} couldn't be parsed`;
}

function emailSent(e) {
    let id = e
    id = getId(id);
    document.querySelector(`#row-${id}`).style.opacity = "50%";
    document.querySelector(`#row-${id}`).style.textDecoration = "line-through";
}