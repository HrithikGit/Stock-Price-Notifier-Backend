function getStarted(){
    console.log("Came Here");
    document.getElementById("mainContent").style.width = '50% !important';
}

function showLoginForm(){
    document.getElementById("loginForm").classList.remove('display-none');
    document.getElementById("registerForm").classList.add('display-none');
}

function showRegisterForm(){
    document.getElementById("registerForm").classList.remove('display-none');
    document.getElementById("loginForm").classList.add('display-none');
}