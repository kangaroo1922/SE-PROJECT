
document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.getElementById('fileInput');
  const preview = document.getElementById('preview');

  fileInput.addEventListener('change', () => {
    //preview.innerHTML = ''; // clear previous previews
    const files = fileInput.files;

    for (const file of files) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const div = document.createElement('div');
        div.classList.add('image-box');
        div.innerHTML = `<img src="${e.target.result}" alt="Vendor photo">`;
        preview.appendChild(div);
      };
      reader.readAsDataURL(file);
    }
  });
});

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



