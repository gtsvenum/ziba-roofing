(function(){
  var f=document.getElementById('estimate-form');if(!f)return;
  var note=document.getElementById('formnote');
  // Success state after the form POSTs and redirects back with ?sent=1
  if(/[?&]sent=1/.test(location.search)){
    note.className='formnote ok';
    note.textContent='Thank you — your request is in. We respond within one business day. For an active leak, call instead.';
    f.reset();
    note.scrollIntoView({block:'center'});
  }
  function clear(el){var w=el.closest('.f');if(!w)return;w.classList.remove('err');
    var m=w.querySelector('.errmsg');if(m)m.remove();}
  function fail(el,msg){var w=el.closest('.f');if(!w)return;w.classList.add('err');
    if(!w.querySelector('.errmsg')){var p=document.createElement('p');
    p.className='errmsg';p.textContent=msg;w.appendChild(p);}}
  f.addEventListener('submit',function(ev){
    var ok=true;
    ['name','phone','email','address'].forEach(function(id){
      var el=document.getElementById(id);clear(el);
      if(!el.value.trim()){fail(el,'Required');ok=false;return;}
      if(id==='email'&&!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(el.value)){
        fail(el,'Enter a valid email');ok=false;}
      if(id==='phone'&&el.value.replace(/\D/g,'').length<10){
        fail(el,'Enter a 10-digit phone number');ok=false;}
    });
    if(!ok){ev.preventDefault();note.className='formnote bad';
      note.textContent='Please fix the highlighted fields.';return;}
    if(!f.getAttribute('action')){
      ev.preventDefault();note.className='formnote bad';
      note.textContent='This form is not connected yet. Please call instead.';return;}
    note.className='formnote';note.textContent='Sending\u2026';
  });
})();
