const firebaseConfig = {
    apiKey: "AIzaSyAFLeG3xlGCH9Ci7j8q6GBA1jDVyb3zSM4",
    authDomain: "utmsmartscan.firebaseapp.com",
    projectId: "utmsmartscan",
    storageBucket: "utmsmartscan.appspot.com",
    messagingSenderId: "150286309478",
    appId: "1:150286309478:web:4ec07841589ecfc34975a7",
    measurementId: "G-276FME46SG"
  };
  
firebase.initializeApp(firebaseConfig);
const auth=firebase.auth()
const database=firebase.database()

function registerStudent(){
    email=documentGetElementById('email').value
    password=documentGetElementById('password').value
    name = documentGetElementById('name').value
    matric = documentGetElementById('matric').value


    if (validate_email(email)==false || validate_password(password)==false){
        alert('Email or Password is Outta Line!!')
        return
    }
    if (validate_field(name)==false || validate_password(password)==false){
        alert('One or more extra field is outta line!!')
    }

    auth.createStudentWIthEmailAndPassword(email,password)
    .then(function(){
    
        var user = auth.currentUser
        var database_ref =database_ref()
        var user_data = {
            email : email,
            name : name,
            matric : matric,
            last_login : Date.now()
        }
        database_ref.child('users/' + user.uid).set(user_data)

        alert("Student created!")

    })
    .catch(function(error){
        var error_code = error.code
        var error_message = error.message

        alert(error_message)
    })
}

function login(){
    var email=documentGetElementById('email').value
   var  password=documentGetElementById('password').value

    if (validate_email(email)==false || validate_password(password)==false){
        alert('Email or Password is Outta Line!!')
        return
    }

    auth.SignInWIthEmailAndPassword(email,password)
    .then(function(){
        var user = auth.currentUser
        var database_ref =database_ref()
        var user_data = {
            last_login : Date.now()
        }
        database_ref.child('users/' + user.uid).update(user_data)

        alert("User Log in!")
        window.location.href = "/isndex.html";

    })



    .catch(function(error){
        var error_code = error.code
        var error_message = error.message

        alert(error_message)
    })
}

function validate_email(email){
    expression = /^[^@]+@\w+(\.\w+)+\w$/
    if (expression.test(email)==true){
        return true
    }else{
        return false
    }
}

function validate_password(password){
    if(password<6){
        return false
    }else{
        return true
    }
}

function validate_field(field){
    if (field==null){
        return false
    }else{
        return true
    }
}