

'use strict';

// Import the functions you need from the SDKs you need
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-app.js";
import {getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut} from "https://www.gstatic.com/firebasejs/9.22.2/firebase-auth.js"

// Your web app's Firebase configuration
const firebaseConfig = {
  
};

window.addEventListener("load", function(){
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    updateUI(document.cookie);
    console.log("hello world load");
    
    // Signup for a new user to firebase
    document.getElementById("sign-up").addEventListener('click', function(){
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        createUserWithEmailAndPassword(auth, email, password)
        .then((userCredential) =>{
            const user = userCredential.user;

            user.getIdToken().then((token) =>{
                document.cookie = "token=" + token + ";path=/;SameSite=Strict";
                window.location = "/";
            });
        })
        .catch((error)=>{
            alert(`Sign Up Error: ${error.message}`);
            console.log(error.code + error.message);
        });
    });

    // Login of a user to firebase
    document.getElementById("login").addEventListener('click', function(){
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        signInWithEmailAndPassword(auth, email, password)
        .then((userCredential) =>{
            const user = userCredential.user;
            console.log("logged in");

            user.getIdToken().then((token) =>{
                document.cookie = "token=" + token + ";path=/;SameSite=Strict";
                window.location = "/";
            });
        })
        .catch((error) => {
            alert(`Login Error: ${error.message}`);
            console.log(error.code + error.message);
        });
    });

    // Sign out from firebase
    document.getElementById("sign-out").addEventListener('click', function(){
        signOut(auth)
        .then((output) => {
            document.cookie = "token=;path=/;SameSite=Strict";
            window.location = "/";
        });
    });
});

function updateUI(cookie){
    var token = parseCookieToken(cookie);

    if(token.length > 0){
        document.getElementById("login-box").hidden = true;
        document.getElementById("sign-out").hidden = false;
    }else {
        document.getElementById("login-box").hidden = false;
        document.getElementById("sign-out").hidden = true;
    }
}

function parseCookieToken(cookie){
    var strings = cookie.split(';');

    for(let i = 0; i < strings.length; i++){
        var temp = strings[i].split('=');
        if(temp[0].trim() === "token")
            return temp[1];
    }

    return "";
}
