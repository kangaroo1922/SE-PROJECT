
//from the first file
const button = document.getElementById('menuButton');
const bar = document.getElementById('slidebar');
const drop = document.getElementById('dropDown');
const submenu = document.getElementById('submenu');
const login = document.getElementById('loginButton');
const drop1 = document.getElementById('dropDown1');
const submenu1 = document.getElementById('submenu1');
button.addEventListener('click' , ()=> {
    bar.classList.toggle('active');
    submenu.classList.remove('active');
    submenu1.classList.remove('active');

});

drop.addEventListener('click' , ()=>{
submenu.classList.toggle('active')
submenu1.classList.remove('active');

});
drop1.addEventListener('click' , ()=>{
submenu1.classList.toggle('active')
submenu.classList.remove('active');
});
login.addEventListener('click' , ()=>{
    let password = document.getElementById('password').value;
    let username = document.getElementById('username').value;
});


