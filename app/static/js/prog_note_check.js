let send_email_button = document.getElementById("send_email_button");
let show_bulk_email = document.getElementById("show_bulk_email")
let bulk_email_form = document.getElementById("bulk_email_form")

show_bulk_email.addEventListener("click", () => {
    console.log(bulk_email_form );
    
    bulk_email_form.classList.contains("hidden") ? bulk_email_form.classList.remove("hidden") : bulk_email_form.classList.add("hidden"); 
})

send_email_button.addEventListener("click", () => {
    send_bulk();
})

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

function send_bulk() {

    let username = document.getElementById("username").value.trim();
    let password = document.getElementById("password").value.trim()

    if (username === "" | password === "") {
        return alert("Username and Password Required")
    }

    if (username && password) {

        const user_credentials = {
            username : username,
            password : password
        }

        fetch('/progress_note_result/send_bulk', {
            method: 'POST',
            body : JSON.stringify(user_credentials)
        })
        .then((data) => {
            data.status === 200 && alert("Reminders sent successfully")
        })
        .catch((err) => {
            console.log(err);
            
        })

    }

    return null;

}