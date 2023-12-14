window.addEventListener('load', function(){

    // Get references to the password input and the checkbox
    var current_password = document.getElementById('password');
    var show_password  = document.getElementById('check');

    // Add an event listener to the checkbox
    show_password.addEventListener('change', function() {

        // Check if the checkbox is checked
        if(this.checked) {
            // If checked, change the password input type to 'text' (show the password)
            current_password.type = 'text';
        } else {
            // If unchecked, change the password input type to 'password' (hide the password)
            current_password.type = 'password';
        }

    });


});


