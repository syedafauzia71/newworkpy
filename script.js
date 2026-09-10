const API = '/products'
const DEFAULT_PRODUCTS = [
  { id:1, name:'Wooden Blocks Set', price:24.99, image_url:'https://picsum.photos/seed/b1/400/300' }
]

function el(q){return document.querySelector(q)}

function renderProducts(list, target){
  const container = document.getElementById(target)
  if(!container) return
  container.innerHTML = ''
  list.forEach(p => {
    const card = document.createElement('div')
    card.className = 'card'
    card.innerHTML = `
      <img src="${p.image_url||'https://picsum.photos/400/300'}" alt="${p.name}">
      <h4 style="margin:10px 0 6px">${p.name}</h4>
      <div class="meta"><div class="price">$${Number(p.price||0).toFixed(2)}</div></div>
    `
    container.appendChild(card)
  })
}

async function load(){
  try{
    const resp = await fetch(API)
    const data = await resp.json()
    const prods = data.products || DEFAULT_PRODUCTS
    renderProducts(prods, 'featured')
    // fetch categories
    try{
      const r2 = await fetch('/categories')
      const d2 = await r2.json()
      const cats = d2.categories || []
      renderCategories(cats)
    }catch(e){
      console.warn('Failed load categories', e)
    }
  }catch(e){
    console.warn('Failed load products', e)
    renderProducts(DEFAULT_PRODUCTS, 'featured')
  }
}

function renderCategories(list){
  const cont = document.getElementById('categories-list')
  if(!cont) return
  cont.innerHTML = ''
  if(!list || list.length === 0){
    cont.innerHTML = '<div style="color:#666">No categories available.</div>'
    return
  }
  list.forEach(c => {
    const a = document.createElement('a')
    a.href = '/products.html'
    a.style.cssText = 'display:inline-block;padding:8px 12px;border-radius:8px;background:#fff;border:1px solid #eee;color:#333;text-decoration:none'
    a.textContent = c.name || c.slug || 'Category'
    cont.appendChild(a)
  })
}

document.addEventListener('DOMContentLoaded', load)
const DEFAULT_PRODUCTS = [
  {id:1,title:'Wooden Blocks Set',price:24.99,img:'https://picsum.photos/seed/b1/400/300'},
  {id:2,title:'Plush Teddy Bear',price:19.5,img:'https://picsum.photos/seed/b2/400/300'},
  {id:3,title:'Mini Race Car',price:14.0,img:'https://picsum.photos/seed/b3/400/300'},
  {id:4,title:'Puzzle 100pcs',price:12.75,img:'https://picsum.photos/seed/b4/400/300'},
  {id:5,title:'Wooden Train',price:29.99,img:'https://picsum.photos/seed/b5/400/300'},
  {id:6,title:'Art Kit for Kids',price:22.5,img:'https://picsum.photos/seed/b6/400/300'}
];

let products = DEFAULT_PRODUCTS.slice();

async function fetchProductsFromApi(){
  try{
    const resp = await fetch('/products');
    if(!resp.ok) throw new Error('Bad response');
    const j = await resp.json();
    if(j && Array.isArray(j.products) && j.products.length){
      products = j.products.map(p=>({
        id: p.id || p.sku || Math.floor(Math.random()*100000),
        title: p.name || p.title || 'Product',
        price: Number(p.price || 0),
        img: p.image_url || p.img || 'https://picsum.photos/400/300?random=1'
      }));
    }
  }catch(e){
    console.warn('Failed to load products from API, using defaults', e);
  }
}

const $ = s=>document.querySelector(s);
const $all = s=>document.querySelectorAll(s);
let cart = {};
if (localStorage.getItem('saeedghani_cart')) {
  cart = JSON.parse(localStorage.getItem('saeedghani_cart')||'{}');
} else if (localStorage.getItem('kinetix_cart')) {
  cart = JSON.parse(localStorage.getItem('kinetix_cart')||'{}');
  localStorage.setItem('saeedghani_cart', JSON.stringify(cart));
}

function renderProducts(){
  const grid = $('#productGrid');
  grid.innerHTML = '';
  products.forEach(p=>{
    const el = document.createElement('div'); el.className='card';
    el.innerHTML = `
      <img src="${p.img}" alt="${p.title}">
      <h4 style="margin:10px 0 6px">${p.title}</h4>
      <div class="meta"><div class="price">$${p.price.toFixed(2)}</div></div>
      <button class="btn add" data-id="${p.id}">Add to cart</button>
    `;
    grid.appendChild(el);
  });
}

function updateCartCount(){
  const count = Object.values(cart).reduce((s,n)=>s+n,0);
  $('#cartCount').textContent = count;
}

function addToCart(id){
  cart[id]= (cart[id]||0)+1;
  saveCart();
  updateCartCount();
  pulseCartCount();
  if ($('#cartModal').getAttribute('aria-hidden') === 'false') renderCartItems();
}

function saveCart(){
  localStorage.setItem('saeedghani_cart', JSON.stringify(cart));
}

function pulseCartCount(){
  const el = $('#cartCount');
  if(!el) return;
  el.classList.add('pulse');
  setTimeout(()=>el.classList.remove('pulse'),600);
}

function openCart(){
  $('#cartModal').setAttribute('aria-hidden','false');
  renderCartItems();
}
function closeCart(){
  $('#cartModal').setAttribute('aria-hidden','true');
}

function renderCartItems(){
  const items = $('#cartItems'); items.innerHTML='';
  let total=0;
  for(const id in cart){
    const qty = cart[id];
    const p = products.find(x=>x.id==id);
    if(!p) continue;
    total += p.price*qty;
    const row = document.createElement('div'); row.className='cart-item';
    row.innerHTML = `
      <img src="${p.img}" alt="">
      <div style="flex:1">
        <div style="font-weight:600">${p.title}</div>
        <div style="color:#666;font-size:.95rem">${qty} × $${p.price.toFixed(2)}</div>
      </div>
      <div style="text-align:right">
        <button data-id="${id}" class="remove">Remove</button>
      </div>
    `;
    items.appendChild(row);
  }
  $('#cartTotal').textContent = total.toFixed(2);
  $all('.remove').forEach(btn=>btn.onclick=e=>{ delete cart[btn.dataset.id]; saveCart(); renderCartItems(); updateCartCount(); });
}

window.addEventListener('DOMContentLoaded',()=>{
  fetchProductsFromApi().then(()=>{
    renderProducts();
    updateCartCount();
  });

  document.body.addEventListener('click',e=>{
    if(e.target.matches('.add')) addToCart(e.target.dataset.id);
    if(e.target.closest('#cartToggle')) openCart();
    if(e.target.closest('#closeCart')) closeCart();
    if(e.target.closest('#checkout')) showCheckout();
    if(e.target.closest('#backToCart')) backToCart();
    if(e.target.closest('#placeOrder')) placeOrder();
  });
});

function showCheckout(){
  const total = parseFloat($('#cartTotal').textContent || '0');
  if(total === 0){ showToast('Your cart is empty'); return; }
  const user = loadUser();
  const form = document.getElementById('checkoutForm');
  if(form){
    form.elements['name'].value = user.name || '';
    form.elements['email'].value = user.email || '';
    form.elements['address'].value = user.address || '';
  }
  clearFieldErrors();
  $('#checkoutView').setAttribute('aria-hidden','false');
  $('#cartItems').style.display='none';
  $('#cartFooter').style.display='none';
  setTimeout(()=>{ const n = form && form.elements['name']; if(n) n.focus(); }, 100);
}

function backToCart(){
  $('#checkoutView').setAttribute('aria-hidden','true');
  $('#cartItems').style.display='block';
  $('#cartFooter').style.display='flex';
}

async function placeOrder(){
  const form = document.getElementById('checkoutForm');
  const data = new FormData(form);
  const name = (data.get('name')||'').toString().trim();
  const email = (data.get('email')||'').toString().trim();
  const address = (data.get('address')||'').toString().trim();
  clearFieldErrors();
  if(!name){ showFieldError(form.elements['name'], 'Name is required'); return; }
  if(!email){ showFieldError(form.elements['email'], 'Email is required'); return; }
  if(!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)){ showFieldError(form.elements['email'], 'Enter a valid email'); return; }

  const orderId = 'SG' + Math.floor(Math.random()*900000+100000);
  const now = new Date().toISOString();

  const items = [];
  for(const id in cart){
    const qty = cart[id];
    const p = products.find(x=>x.id==id);
    if(!p) continue;
    items.push({title: p.title, qty, price: p.price});
  }

  const grandTotal = Number(Object.keys(cart).reduce((s,id)=>{
    const p = products.find(x=>x.id==id); return s + (p? p.price*cart[id]:0);
  },0).toFixed(2));

  const payload = {
    order_id: orderId,
    date: now,
    name,
    email,
    address,
    items,
    total: grandTotal
  };

  let serverSaved = false;
  try{
    const resp = await fetch('http://localhost:5000/orders', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    serverSaved = resp && resp.ok;
  }catch(e){ serverSaved = false; }

  if(!serverSaved){
    enqueueOrder(payload);
    showToast(`Order ${orderId} queued — will send when server is available`);
  } else {
    showToast(`Order ${orderId} saved to server — thank you, ${name}!`);
  }

  saveUser({name, email, address});
  cart = {};
  saveCart();
  renderCartItems();
  updateCartCount();
  backToCart();
  closeCart();
}

function getQueuedOrders(){
  try{ return JSON.parse(localStorage.getItem('saeedghani_order_queue')||'[]'); }catch(e){ return []; }
}
function setQueuedOrders(arr){
  try{ localStorage.setItem('saeedghani_order_queue', JSON.stringify(arr)); }catch(e){}
}
function enqueueOrder(order){
  const q = getQueuedOrders(); q.push(order); setQueuedOrders(q);
}

async function sendQueuedOrders(){
  const q = getQueuedOrders();
  if(!q.length) return;
  const remaining = [];
  for(const o of q){
    try{
      const resp = await fetch('http://localhost:5000/orders', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(o)});
      if(!resp.ok) remaining.push(o);
    }catch(e){ remaining.push(o); }
  }
  setQueuedOrders(remaining);
  if(remaining.length === 0 && q.length>0) showToast('Queued orders successfully sent to server');
}

window.addEventListener('DOMContentLoaded', ()=>{
  setTimeout(()=>sendQueuedOrders(), 2000);
  setInterval(()=>sendQueuedOrders(), 30000);
});

function showToast(msg){
  const t = document.createElement('div');
  t.className = 'toast';
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(()=>{ t.classList.add('visible'); }, 20);
  setTimeout(()=>{ t.classList.remove('visible'); setTimeout(()=>t.remove(),300); }, 3000);
}

function loadUser(){
  try{ return JSON.parse(localStorage.getItem('saeedghani_user')||'{}'); }catch(e){return{}}
}
function saveUser(user){
  try{ localStorage.setItem('saeedghani_user', JSON.stringify(user)); }catch(e){}
}

function clearFieldErrors(){
  $all('.field-error').forEach(e=>e.remove());
}

function showFieldError(input, msg){
  clearFieldErrors();
  const span = document.createElement('div');
  span.className = 'field-error';
  span.textContent = msg;
  input.insertAdjacentElement('afterend', span);
}
