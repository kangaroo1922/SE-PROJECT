const button = document.getElementById('button');
const bar = document.getElementById('slidebar');
const submenu = document.getElementById('submenu');
const drop = document.getElementById('dropDown');
const submenu1 = document.getElementById('submenu1');
const drop1 = document.getElementById('dropDown1');
button.addEventListener('click' , ()=>{
    bar.classList.toggle('active');
    submenu.classList.remove('active');
    submenu1.classList.remove('active');
});
drop.addEventListener('click' , ()=>{
    submenu.classList.toggle('active');
    submenu1.classList.remove('active');

});
drop1.addEventListener('click' , ()=>{
    submenu1.classList.toggle('active');
    submenu.classList.remove('active');
});


