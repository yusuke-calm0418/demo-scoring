// function togglePassword() {
//     var passwordField = document.getElementById("password");
//     var eyeIcon = document.getElementById("eye-icon");
//     if (passwordField.type === "password") {
//         passwordField.type = "text";
//         eyeIcon.innerHTML = '<path d="M10 3C5 3 1.73 7.11 1 10c.73 2.89 4 7 9 7s8.27-4.11 9-7c-.73-2.89-4-7-9-7zm0 12c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>';
//     } else {
//         passwordField.type = "password";
//         eyeIcon.innerHTML = '<path d="M2.33 1.47a9.41 9.41 0 00-1.8 8.44c.73 2.89 4 7 9 7 2.5 0 4.83-1.18 6.67-3.12l1.31 1.31a.75.75 0 101.06-1.06L3.39 1.47a.75.75 0 10-1.06 1.06zM10 15c-4.27 0-7.29-3.11-8-5.76C2.71 6.38 6.07 3.25 10 3c1.52 0 2.97.49 4.25 1.39L6.53 12.1A5.97 5.97 0 0110 15zm7.67-1.33c-.3.76-.73 1.48-1.26 2.12a8.38 8.38 0 00.91-4.03c-.73-2.89-4-7-9-7-1.52 0-2.97.49-4.25 1.39l1.56 1.56A5.97 5.97 0 0110 9c4.27 0 7.29 3.11 8 5.76.24-.36.45-.75.67-1.16zM10 5c-.28 0-.55.02-.82.05a6.01 6.01 0 00-1.24 3.28l5.1 5.1A5.97 5.97 0 0010 5zm-3.91.91l.03.03-.03-.03z"/>';
//     }
// }

// function togglePassword() {
//         var passwordField = document.querySelector("input[name='password']");
//         var eyeIcon = document.getElementById("eye-icon");
//         if (passwordField.type === "password") {
//             passwordField.type = "text";
//             eyeIcon.setAttribute("fill", "#00f");  // 目のアイコンを青に
//         } else {
//             passwordField.type = "password";
//             eyeIcon.setAttribute("fill", "#555");  // アイコンを元の色に
//         }
//     }

console.log("main.js is loaded");


function togglePassword() {
    var passwordField = document.getElementById("password-field");
    var eyeIcon = document.getElementById("eye-icon");
    if (passwordField.type === "password") {
        passwordField.type = "text";
        eyeIcon.setAttribute("fill", "#00f");  // アイコンの色を変更
    } else {
        passwordField.type = "password";
        eyeIcon.setAttribute("fill", "#555");  // 元の色に戻す
    }
}
