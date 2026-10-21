const state = {
  token: sessionStorage.getItem("yaotel-token"),
  email: sessionStorage.getItem("yaotel-email"),
  accountMode: "login",
};

const roomImages = {
  Standard: "/static/rooms/standard.png",
  Deluxe: "/static/rooms/deluxe.png",
  Family: "/static/rooms/family.png",
  Suite: "/static/rooms/suite.png",
};

const roomCategoryNames = {
  Standard: "Стандарт",
  Deluxe: "Делюкс",
  Family: "Семейный",
  Suite: "Люкс",
};

const elements = {
  apiState: document.querySelector("#api-state"),
  searchForm: document.querySelector("#search-form"),
  checkIn: document.querySelector("#check-in"),
  checkOut: document.querySelector("#check-out"),
  guests: document.querySelector("#guests"),
  roomList: document.querySelector("#room-list"),
  resultsSummary: document.querySelector("#results-summary"),
  accountForm: document.querySelector("#account-form"),
  accountGuest: document.querySelector("#account-guest"),
  accountMember: document.querySelector("#account-member"),
  accountTitle: document.querySelector("#account-title"),
  accountMessage: document.querySelector("#account-message"),
  accountSubmit: document.querySelector("#account-submit"),
  email: document.querySelector("#email"),
  password: document.querySelector("#password"),
  memberEmail: document.querySelector("#member-email"),
  passwordHint: document.querySelector("#password-hint"),
  toast: document.querySelector("#toast"),
  roomsTab: document.querySelector("#rooms-tab"),
  bookingsTab: document.querySelector("#bookings-tab"),
  roomsView: document.querySelector("#rooms-view"),
  bookingsView: document.querySelector("#bookings-view"),
  bookingList: document.querySelector("#booking-list"),
};

const localDate = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

function setDefaultDates() {
  const today = new Date();
  const checkIn = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1);
  const checkOut = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 3);
  elements.checkIn.value = localDate(checkIn);
  elements.checkOut.value = localDate(checkOut);
  elements.checkIn.min = localDate(checkIn);
  elements.checkOut.min = localDate(new Date(checkIn.getFullYear(), checkIn.getMonth(), checkIn.getDate() + 1));
  updateTripSummary();
}

function formatDate(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "short" }).format(new Date(`${value}T12:00:00`));
}

function formatPrice(kopecks) {
  return new Intl.NumberFormat("ru-RU", { style: "currency", currency: "RUB", maximumFractionDigits: 0 }).format(kopecks / 100);
}

function nightsCount() {
  const start = new Date(`${elements.checkIn.value}T00:00:00`);
  const end = new Date(`${elements.checkOut.value}T00:00:00`);
  return Math.max(1, Math.round((end - start) / 86400000));
}

function updateTripSummary() {
  document.querySelector("#summary-check-in").textContent = formatDate(elements.checkIn.value);
  document.querySelector("#summary-check-out").textContent = formatDate(elements.checkOut.value);
  document.querySelector("#summary-guests").textContent = `${elements.guests.value} ${guestWord(Number(elements.guests.value))}`;
}

function guestWord(count) {
  if (count % 10 === 1 && count % 100 !== 11) return "гость";
  if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return "гостя";
  return "гостей";
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("Accept", "application/json");
  if (options.body) headers.set("Content-Type", "application/json");
  if (state.token) headers.set("Authorization", `Bearer ${state.token}`);
  const response = await fetch(path, { ...options, headers });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail;
    throw new Error(typeof detail === "string" ? detail : "Не удалось выполнить запрос. Проверьте введенные данные.");
  }
  return data;
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("is-visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => elements.toast.classList.remove("is-visible"), 3200);
}

function setAccountMessage(message = "", type = "") {
  elements.accountMessage.textContent = message;
  elements.accountMessage.className = `form-message${type ? ` is-${type}` : ""}`;
}

function setAccountMode(mode) {
  state.accountMode = mode;
  const isRegister = mode === "register";
  document.querySelector("#login-mode").classList.toggle("is-selected", !isRegister);
  document.querySelector("#register-mode").classList.toggle("is-selected", isRegister);
  elements.accountTitle.textContent = state.token
    ? "Личный кабинет"
    : isRegister
      ? "Создайте аккаунт"
      : "Войдите в профиль";
  elements.accountSubmit.textContent = isRegister ? "Создать аккаунт" : "Войти";
  elements.password.autocomplete = isRegister ? "new-password" : "current-password";
  elements.password.minLength = isRegister ? 12 : 1;
  elements.passwordHint.hidden = !isRegister;
  setAccountMessage();
}

function renderAccount() {
  const signedIn = Boolean(state.token);
  elements.accountGuest.hidden = signedIn;
  elements.accountMember.hidden = !signedIn;
  elements.accountTitle.textContent = signedIn
    ? "Личный кабинет"
    : state.accountMode === "register"
      ? "Создайте аккаунт"
      : "Войдите в профиль";
  if (signedIn) elements.memberEmail.textContent = state.email || "Аккаунт ЯОтель";
}

function setApiState(online, message) {
  elements.apiState.classList.toggle("is-online", online);
  elements.apiState.classList.toggle("is-offline", !online);
  elements.apiState.lastElementChild.textContent = message;
}

function roomCard(room) {
  const article = document.createElement("article");
  article.className = "room-card";
  const image = document.createElement("img");
  image.className = "room-photo";
  image.src = roomImages[room.category] || roomImages.Standard;
  image.alt = `Интерьер номера категории ${roomCategoryNames[room.category] || room.category}`;
  image.loading = "lazy";
  image.onerror = () => { image.hidden = true; };

  const details = document.createElement("div");
  details.className = "room-details";
  const number = document.createElement("p");
  number.className = "room-number";
  number.textContent = `Номер ${room.number}`;
  const name = document.createElement("h3");
  name.className = "room-name";
  name.textContent = roomCategoryNames[room.category] || room.category;
  const meta = document.createElement("div");
  meta.className = "room-meta";
  const capacity = document.createElement("span");
  capacity.textContent = `До ${room.capacity} ${guestWord(room.capacity)}`;
  const dates = document.createElement("span");
  dates.textContent = `${nightsCount()} ${nightWord(nightsCount())}`;
  meta.append(capacity, dates);
  const availability = document.createElement("span");
  availability.className = "room-status";
  availability.textContent = room.status === "clean" ? "Готов к заселению" : "Доступен для бронирования";
  details.append(number, name, meta, availability);

  const action = document.createElement("div");
  action.className = "room-action";
  const price = document.createElement("div");
  price.innerHTML = `<span class="room-price">${formatPrice(room.base_price_kopecks)}</span><span class="price-unit"> / ночь</span>`;
  const book = document.createElement("button");
  book.className = "button button-outline";
  book.type = "button";
  book.textContent = "Забронировать";
  book.addEventListener("click", () => createBooking(room, book));
  action.append(price, book);
  article.append(image, details, action);
  return article;
}

function nightWord(count) {
  const n = Math.abs(count) % 100;
  const digit = n % 10;
  if (n > 10 && n < 20) return "ночей";
  if (digit > 1 && digit < 5) return "ночи";
  return digit === 1 ? "ночь" : "ночей";
}

async function searchRooms() {
  updateTripSummary();
  elements.roomList.innerHTML = '<div class="loading-row"><span class="spinner"></span>Ищем доступные номера</div>';
  elements.resultsSummary.textContent = "Запрос к каталогу номеров";
  const params = new URLSearchParams({
    check_in: elements.checkIn.value,
    check_out: elements.checkOut.value,
    guests: elements.guests.value,
  });
  try {
    const rooms = await request(`/api/rooms/availability?${params}`);
    elements.roomList.replaceChildren();
    if (rooms.length === 0) {
      elements.roomList.innerHTML = '<div class="empty-state">На выбранные даты свободных номеров нет. Попробуйте изменить даты или число гостей.</div>';
      elements.resultsSummary.textContent = "Свободных номеров не найдено";
      return;
    }
    rooms.forEach((room) => elements.roomList.append(roomCard(room)));
    elements.resultsSummary.textContent = `${rooms.length} ${roomWord(rooms.length)} на выбранные даты`;
    setApiState(true, "API доступно");
  } catch (error) {
    elements.roomList.innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`;
    elements.resultsSummary.textContent = "Не удалось получить список номеров";
    setApiState(false, "API недоступно");
  }
}

function roomWord(count) {
  if (count % 10 === 1 && count % 100 !== 11) return "номер";
  if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return "номера";
  return "номеров";
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

async function createBooking(room, button) {
  if (!state.token) {
    setAccountMessage("Войдите или зарегистрируйтесь, чтобы оформить бронь.", "error");
    elements.email.focus();
    showToast("Для бронирования войдите в профиль");
    return;
  }
  button.disabled = true;
  button.textContent = "Оформляем…";
  try {
    const booking = await request("/api/bookings", {
      method: "POST",
      body: JSON.stringify({
        room_id: room.id,
        check_in: elements.checkIn.value,
        check_out: elements.checkOut.value,
        guests: Number(elements.guests.value),
      }),
    });
    showToast(`Бронь создана: ${booking.id}`);
    await openBookings();
  } catch (error) {
    showToast(error.message);
    button.disabled = false;
    button.textContent = "Забронировать";
  }
}

async function accountAction(event) {
  event.preventDefault();
  const isRegister = state.accountMode === "register";
  elements.accountSubmit.disabled = true;
  setAccountMessage(isRegister ? "Создаем аккаунт…" : "Выполняем вход…");
  const email = elements.email.value.trim();
  const password = elements.password.value;
  try {
    if (isRegister) {
      await request("/api/auth/register", { method: "POST", body: JSON.stringify({ email, password }) });
    }
    const token = await request("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
    state.token = token.access_token;
    state.email = email;
    sessionStorage.setItem("yaotel-token", state.token);
    sessionStorage.setItem("yaotel-email", state.email);
    renderAccount();
    setAccountMessage(isRegister ? "Аккаунт создан." : "Вход выполнен.", "success");
    showToast(isRegister ? "Аккаунт создан, вы вошли" : "Вы вошли в профиль");
    await openBookings();
  } catch (error) {
    setAccountMessage(error.message, "error");
  } finally {
    elements.accountSubmit.disabled = false;
  }
}

async function openBookings() {
  elements.roomsView.hidden = true;
  elements.bookingsView.hidden = false;
  elements.roomsTab.classList.remove("is-active");
  elements.bookingsTab.classList.add("is-active");
  if (!state.token) {
    elements.bookingList.innerHTML = '<div class="empty-state">Войдите в профиль, чтобы увидеть свои бронирования.</div>';
    return;
  }
  elements.bookingList.innerHTML = '<div class="loading-row"><span class="spinner"></span>Загружаем бронирования</div>';
  try {
    const bookings = await request("/api/bookings");
    renderBookings(bookings);
  } catch (error) {
    elements.bookingList.innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`;
  }
}

function renderBookings(bookings) {
  elements.bookingList.replaceChildren();
  if (bookings.length === 0) {
    elements.bookingList.innerHTML = '<div class="empty-state">У вас пока нет бронирований.</div>';
    return;
  }
  const list = document.createElement("div");
  list.className = "booking-list";
  for (const booking of bookings) {
    const row = document.createElement("article");
    row.className = "booking-row";
    const main = document.createElement("div");
    main.className = "booking-main";
    const title = document.createElement("strong");
    title.textContent = `Бронь ${booking.id.slice(0, 8)}`;
    const dates = document.createElement("span");
    dates.textContent = `${formatDate(booking.check_in)} — ${formatDate(booking.check_out)} · ${booking.guests} ${guestWord(booking.guests)}`;
    main.append(title, dates);
    const total = document.createElement("span");
    total.className = "booking-total";
    total.textContent = formatPrice(booking.total_price_kopecks);
    const status = document.createElement("span");
    status.className = `status-label${booking.status === "cancelled" ? " cancelled" : ""}`;
    status.textContent = booking.status === "cancelled" ? "Отменена" : booking.status === "confirmed" ? "Подтверждена" : booking.status;
    row.append(main, total, status);
    if (booking.status !== "cancelled") {
      const cancel = document.createElement("button");
      cancel.className = "button button-outline";
      cancel.type = "button";
      cancel.textContent = "Отменить";
      cancel.addEventListener("click", async () => {
        cancel.disabled = true;
        try {
          await request(`/api/bookings/${encodeURIComponent(booking.id)}`, { method: "DELETE" });
          showToast("Бронирование отменено");
          await openBookings();
        } catch (error) {
          showToast(error.message);
          cancel.disabled = false;
        }
      });
      row.append(cancel);
    }
    list.append(row);
  }
  elements.bookingList.append(list);
}

function showRooms() {
  elements.bookingsView.hidden = true;
  elements.roomsView.hidden = false;
  elements.bookingsTab.classList.remove("is-active");
  elements.roomsTab.classList.add("is-active");
}

async function checkApi() {
  try {
    await request("/health");
    setApiState(true, "API доступно");
  } catch {
    setApiState(false, "API недоступно");
  }
}

elements.searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (elements.checkOut.value <= elements.checkIn.value) {
    showToast("Дата выезда должна быть позже даты заезда");
    return;
  }
  searchRooms();
});
elements.checkIn.addEventListener("change", () => {
  const nextDay = new Date(`${elements.checkIn.value}T00:00:00`);
  nextDay.setDate(nextDay.getDate() + 1);
  elements.checkOut.min = localDate(nextDay);
  if (elements.checkOut.value <= elements.checkIn.value) elements.checkOut.value = localDate(nextDay);
  updateTripSummary();
});
elements.checkOut.addEventListener("change", updateTripSummary);
elements.guests.addEventListener("change", updateTripSummary);
elements.accountForm.addEventListener("submit", accountAction);
document.querySelector("#login-mode").addEventListener("click", () => setAccountMode("login"));
document.querySelector("#register-mode").addEventListener("click", () => setAccountMode("register"));
document.querySelector("#logout").addEventListener("click", () => {
  state.token = null;
  state.email = null;
  sessionStorage.removeItem("yaotel-token");
  sessionStorage.removeItem("yaotel-email");
  renderAccount();
  setAccountMessage("Вы вышли из профиля.");
  showToast("Сеанс завершен");
  showRooms();
});
document.querySelector("#refresh-rooms").addEventListener("click", searchRooms);
document.querySelector("#refresh-bookings").addEventListener("click", openBookings);
elements.roomsTab.addEventListener("click", showRooms);
elements.bookingsTab.addEventListener("click", openBookings);

setDefaultDates();
renderAccount();
checkApi();
searchRooms();
