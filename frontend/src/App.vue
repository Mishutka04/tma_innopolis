<template>
  <div class="app-container">
    <!-- Добавляем мета-тег для Telegram WebApp -->
    <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no" />

    <!-- Экран выбора роли -->
    <div v-if="!isAuthenticated" class="auth-screen">
      <div class="auth-form">
        <h2>Вход в систему</h2>
        <div class="form-group">
          <label>Выберите роль:</label>
          <div class="role-selector">
            <button 
              @click="selectRole('organizer')"
              :class="{ active: selectedRole === 'organizer' }"
            >
              Организатор
            </button>
            <button 
              @click="selectRole('admin')"
              :class="{ active: selectedRole === 'admin' }"
            >
              Администратор
            </button>
          </div>
        </div>
        <div class="form-group">
          <label for="auth-name">Ваше имя:</label>
          <input 
            id="auth-name"
            v-model="userName"
            type="text"
            placeholder="Введите ваше имя"
          >
        </div>
        <div class="error-message" v-if="authError">{{ authError }}</div>
        <button 
          class="login-btn" 
          @click="login"
          :disabled="!selectedRole || !userName"
        >
          Войти
        </button>
      </div>
    </div>

    <!-- Основной контент приложения -->
    <div v-else>
      <header>
        <div class="user-info">
          <span>{{ currentUser.name }} ({{ currentUser.role === 'admin' ? 'Администратор' : 'Организатор' }})</span>
          <button class="logout-btn" @click="logout">Выйти</button>
        </div>
        <h1>Календарь мероприятий</h1>
        <div class="calendar-filters">
          <div class="filter-group">
            <label>Просмотр:</label>
            <div class="button-group">
              <button 
                @click="currentView = 'day'" 
                :class="{ active: currentView === 'day' }"
              >День</button>
              <button 
                @click="currentView = 'month'" 
                :class="{ active: currentView === 'month' }"
              >Месяц</button>
              <button 
                @click="currentView = 'year'" 
                :class="{ active: currentView === 'year' }"
              >Год</button>
            </div>
          </div>
          <div class="date-selector">
            <button @click="navigateDate(-1)">
              <i class="icon">&#9664;</i>
            </button>
            <span v-if="currentView === 'day'">{{ formatDate(currentDate) }}</span>
            <span v-else-if="currentView === 'month'">{{ formatMonth(currentDate) }}</span>
            <span v-else>{{ currentDate.getFullYear() }}</span>
            <button @click="navigateDate(1)">
              <i class="icon">&#9654;</i>
            </button>
          </div>
          <div class="room-filter">
            <label for="room-select">Помещение:</label>
            <select 
              id="room-select" 
              v-model="selectedRoom"
              class="room-select"
            >
              <option value="">Все помещения</option>
              <option 
                v-for="room in rooms" 
                :key="room.id" 
                :value="room.id"
              >
                {{ room.name }}
              </option>
            </select>
          </div>
        </div>
        <button class="create-event-btn" @click="openEventModal()">Создать мероприятие</button>
      </header>

      <main>
        <!-- Календарь - Дневной вид -->
        <div v-if="currentView === 'day'" class="day-view">
          <div class="time-slots">
            <div v-for="hour in 24" :key="`hour-${hour-1}`" class="time-slot">
              <div class="time-label">{{ formatHour(hour-1) }}</div>
              <div class="time-content">
                <div 
                  v-for="event in getEventsForHour(hour-1)" 
                  :key="event.id"
                  class="event-card"
                  :class="[
                    getStatusClass(event.status),
                    { 'not-editable': !canEditEvent(event) }
                  ]"
                  :style="getEventStyle(event)"
                  @click="handleEventClick(event)"
                >
                  <div class="event-time">{{ formatEventTime(event) }}</div>
                  <div class="event-title">{{ event.title }}</div>
                  <div class="event-organizer">Организатор: {{ event.organizerName }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Календарь - Месячный вид -->
        <div v-else-if="currentView === 'month'" class="month-view">
          <div class="weekdays">
            <div v-for="day in weekdays" :key="day" class="weekday">{{ day }}</div>
          </div>
          <div class="month-grid">
            <div 
              v-for="(day, index) in getDaysInMonth()" 
              :key="index"
              class="day-cell"
              :class="{ 'other-month': day.otherMonth, 'today': isToday(day.date) }"
              @click="selectDay(day.date)"
            >
              <div class="day-number">{{ day.date.getDate() }}</div>
              <div class="day-events">
                <div 
                  v-for="event in getEventsForDay(day.date)" 
                  :key="event.id"
                  class="month-event-indicator"
                  :class="[
                    getStatusClass(event.status),
                    { 'not-editable': !canEditEvent(event) }
                  ]"
                  @click.stop="handleEventClick(event)"
                >
                  {{ event.title }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Календарь - Годовой вид -->
        <div v-else class="year-view">
          <div 
            v-for="month in 12" 
            :key="month"
            class="year-month"
            @click="selectMonth(month - 1)"
          >
            <h3>{{ getMonthName(month - 1) }}</h3>
            <div class="month-preview">
              <div 
                v-for="event in getEventsForMonth(month - 1)" 
                :key="event.id"
                class="year-event-indicator"
                :class="getStatusClass(event.status)"
              ></div>
            </div>
          </div>
        </div>
      </main>

      <!-- Модальное окно для создания/редактирования мероприятия -->
      <div v-if="showEventModal" class="modal-overlay" @click="closeEventModal">
        <div class="modal-content" @click.stop>
          <h2>{{ isEditMode ? 'Редактирование мероприятия' : 'Создание мероприятия' }}</h2>
          
          <div class="form-group">
            <label for="event-title">Название мероприятия:</label>
            <input 
              id="event-title" 
              v-model="currentEvent.title" 
              type="text" 
              placeholder="Введите название мероприятия"
            >
          </div>
          
          <div class="form-group">
            <label for="event-fullname">ФИО:</label>
            <input 
              id="event-fullname" 
              v-model="currentEvent.fullName" 
              type="text" 
              placeholder="Введите ФИО"
            >
          </div>
          
          <div class="form-group">
            <label for="event-phone">Телефон:</label>
            <input 
              id="event-phone" 
              v-model="currentEvent.phone" 
              type="text" 
              placeholder="Введите номер телефона"
            >
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label for="event-start">Время начала:</label>
              <input 
                id="event-start" 
                v-model="currentEvent.startTime" 
                type="datetime-local"
              >
            </div>
            
            <div class="form-group">
              <label for="event-end">Время окончания:</label>
              <input 
                id="event-end" 
                v-model="currentEvent.endTime" 
                type="datetime-local"
              >
            </div>
          </div>
          
          <div class="form-group">
            <label>Вид мероприятия:</label>
            <div class="radio-group">
              <label class="radio-label">
                <input 
                  type="radio" 
                  v-model="currentEvent.eventType" 
                  value="closed"
                > Закрытое
              </label>
              <label class="radio-label">
                <input 
                  type="radio" 
                  v-model="currentEvent.eventType" 
                  value="open"
                > Открытое
              </label>
            </div>
          </div>
          
          <div class="form-group">
            <label class="checkbox-label">
              <input 
                type="checkbox" 
                v-model="currentEvent.isCommercial"
              > Коммерческое мероприятие
            </label>
          </div>
          
          <div class="form-group">
            <label>Количество человек:</label>
            <div class="radio-group">
              <label 
                v-for="option in attendeesOptions" 
                :key="option" 
                class="radio-label"
              >
                <input 
                  type="radio" 
                  v-model="currentEvent.attendeesCount" 
                  :value="option"
                > {{ option }}
              </label>
            </div>
          </div>
          
          <div class="form-group">
            <label for="event-tech">Доп тех организации:</label>
            <textarea 
              id="event-tech" 
              v-model="currentEvent.technicalRequirements" 
              placeholder="Укажите технические требования"
            ></textarea>
          </div>
          
          <div class="form-group">
            <label for="event-catering">Питание:</label>
            <textarea 
              id="event-catering" 
              v-model="currentEvent.catering" 
              placeholder="Укажите требования к питанию"
            ></textarea>
          </div>
          
          <div class="form-group">
            <label for="event-description">Краткий анонс:</label>
            <textarea 
              id="event-description" 
              v-model="currentEvent.description" 
              placeholder="Введите краткий анонс мероприятия"
            ></textarea>
          </div>
          
          <div class="form-group">
            <label for="event-room">Помещение:</label>
            <select 
              id="event-room" 
              v-model="currentEvent.room"
              class="room-select"
              required
            >
              <option value="">Выберите помещение</option>
              <option 
                v-for="room in rooms" 
                :key="room.id" 
                :value="room.id"
              >
                {{ room.name }}
              </option>
            </select>
          </div>
          
          <div class="error-message" v-if="errorMessage">{{ errorMessage }}</div>
          
          <div class="modal-actions">
            <button class="close-btn" @click="closeEventModal">Закрыть</button>
            
            <div v-if="isEditMode" class="action-buttons">
              <button 
                v-if="canDeleteEvent"
                class="delete-btn" 
                @click="deleteEvent"
              >
                Удалить
              </button>
              
              <button 
                v-if="currentUser.role === 'admin'"
                class="accept-btn" 
                @click="acceptEvent"
                :disabled="currentEvent.status === 'accepted'"
              >
                Принять запись
              </button>
            </div>
            
            <button 
              class="save-btn" 
              @click="saveEvent"
              :disabled="!currentEvent.room"
            >
              Сохранить
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

// Добавляем объект для Telegram WebApp
const telegram = window.Telegram.WebApp;

// Состояние приложения
const events = ref([]);
const currentView = ref('month');
const currentDate = ref(new Date());
const showEventModal = ref(false);
const isEditMode = ref(false);
const currentUser = ref({
  role: '',
  id: '',
  name: ''
});
const currentEvent = ref({
  id: null,
  title: '',
  fullName: '',
  phone: '',
  startTime: '',
  endTime: '',
  eventType: 'closed', // 'closed' или 'open'
  isCommercial: false,
  attendeesCount: '', // '0-10', '11-30', '31-50', '51-100', '100+'
  technicalRequirements: '',
  catering: '',
  description: '',
  status: 'start',
  comments: [],
  organizerId: '', // ID создателя события
  organizerName: '', // Добавляем имя организатора
  room: '',
});
const newComment = ref('');
const errorMessage = ref('');

// Состояние авторизации
const isAuthenticated = ref(false);
const selectedRole = ref('');
const userName = ref('');
const authError = ref('');

// Добавляем список помещений
const rooms = [
  { id: '101', name: 'Конференц-зал "Иннополис" (101)' },
  { id: '102', name: 'Переговорная "Технопарк" (102)' },
  { id: '201', name: 'Учебная аудитория "Байтик" (201)' },
  { id: '202', name: 'Лекционный зал "IT-парк" (202)' },
  { id: '301', name: 'Коворкинг "Стартап" (301)' },
  { id: '302', name: 'Мультимедийная студия (302)' },
  { id: '401', name: 'Конференц-зал "Цифра" (401)' },
  { id: '402', name: 'Тренинг-центр "Прогресс" (402)' }
];

// Добавляем состояние для выбранного помещения
const selectedRoom = ref('');

// Константы
const weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
const monthNames = [
  'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
];

// Константы для количества участников
const attendeesOptions = [
  '0-10',
  '11-30',
  '31-50',
  '51-100',
  '100+'
];

// Модифицируем onMounted для инициализации Telegram WebApp
onMounted(() => {
  // Инициализируем Telegram WebApp
  telegram.ready();
  
  // Получаем данные пользователя
  const user = telegram.initDataUnsafe?.user;
  if (user) {
    console.log('Telegram user ID:', user.id);
    // Можно отправить уведомление через alert или использовать встроенный функционал TWA
    telegram.showAlert(`Ваш Telegram ID: ${user.id}`);
    
    // Можно также автоматически заполнить данные пользователя
    currentUser.value = {
      role: '', // роль пока оставляем пустой, пользователь выберет сам
      id: user.id.toString(),
      name: user.first_name + (user.last_name ? ' ' + user.last_name : '')
    };
    userName.value = currentUser.value.name; // Заполняем поле имени
  }

  // Существующий код инициализации тестовых данных
  const now = new Date();
  const tomorrow = new Date();
  tomorrow.setDate(now.getDate() + 1);
  
  events.value = [
    {
      id: 1,
      title: 'Совещание команды',
      description: 'Еженедельное совещание команды разработки',
      startTime: formatDateTimeForInput(new Date(now.getFullYear(), now.getMonth(), now.getDate(), 10, 0)),
      endTime: formatDateTimeForInput(new Date(now.getFullYear(), now.getMonth(), now.getDate(), 12, 0)),
      telegramUser: '@manager',
      room: '301',
      status: 'start',
      comments: [
        { text: 'Подготовить отчет о проделанной работе', date: new Date(now.getTime() - 86400000) }
      ],
      organizerId: '1',
      organizerName: 'Иван Петров',
    },
    {
      id: 2,
      title: 'Презентация проекта',
      description: 'Презентация нового проекта для клиента',
      startTime: formatDateTimeForInput(new Date(now.getFullYear(), now.getMonth(), now.getDate(), 14, 0)),
      endTime: formatDateTimeForInput(new Date(now.getFullYear(), now.getMonth(), now.getDate(), 16, 0)),
      telegramUser: '@projectlead',
      room: '405',
      status: 'processing',
      comments: [],
      organizerId: '2',
      organizerName: 'Анна Иванова',
    },
    {
      id: 3,
      title: 'Тренинг по Vue 3',
      description: 'Обучение команды новым возможностям Vue 3',
      startTime: formatDateTimeForInput(new Date(tomorrow.getFullYear(), tomorrow.getMonth(), tomorrow.getDate(), 11, 0)),
      endTime: formatDateTimeForInput(new Date(tomorrow.getFullYear(), tomorrow.getMonth(), tomorrow.getDate(), 13, 30)),
      telegramUser: '@trainer',
      room: '201',
      status: 'start',
      comments: [],
      organizerId: '3',
      organizerName: 'Сергей Петров',
    }
  ];
});

// Вспомогательные функции для форматирования дат
function formatDate(date) {
  return `${date.getDate()} ${monthNames[date.getMonth()]} ${date.getFullYear()}`;
}

function formatMonth(date) {
  return `${monthNames[date.getMonth()]} ${date.getFullYear()}`;
}

function formatHour(hour) {
  return `${hour.toString().padStart(2, '0')}:00`;
}

function formatEventTime(event) {
  const start = new Date(event.startTime);
  const end = new Date(event.endTime);
  return `${start.getHours().toString().padStart(2, '0')}:${start.getMinutes().toString().padStart(2, '0')} - ${end.getHours().toString().padStart(2, '0')}:${end.getMinutes().toString().padStart(2, '0')}`;
}

function formatCommentDate(date) {
  return new Date(date).toLocaleString('ru-RU');
}

function formatDateTimeForInput(date) {
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

// Функции для работы с календарем
function navigateDate(direction) {
  const newDate = new Date(currentDate.value);
  
  if (currentView.value === 'day') {
    newDate.setDate(newDate.getDate() + direction);
  } else if (currentView.value === 'month') {
    newDate.setMonth(newDate.getMonth() + direction);
  } else {
    newDate.setFullYear(newDate.getFullYear() + direction);
  }
  
  currentDate.value = newDate;
}

function getMonthName(month) {
  return monthNames[month];
}

function getDaysInMonth() {
  const year = currentDate.value.getFullYear();
  const month = currentDate.value.getMonth();
  
  // Первый день месяца
  const firstDay = new Date(year, month, 1);
  // Последний день месяца
  const lastDay = new Date(year, month + 1, 0);
  
  // Получаем день недели для первого дня (0 - воскресенье, 1 - понедельник, и т.д.)
  let firstDayOfWeek = firstDay.getDay();
  // Преобразуем в формат, где понедельник - 0, воскресенье - 6
  firstDayOfWeek = firstDayOfWeek === 0 ? 6 : firstDayOfWeek - 1;
  
  const daysArray = [];
  
  // Добавляем дни предыдущего месяца
  const prevMonth = new Date(year, month, 0);
  const prevMonthDays = prevMonth.getDate();
  
  for (let i = firstDayOfWeek - 1; i >= 0; i--) {
    daysArray.push({
      date: new Date(year, month - 1, prevMonthDays - i),
      otherMonth: true
    });
  }
  
  // Добавляем дни текущего месяца
  for (let i = 1; i <= lastDay.getDate(); i++) {
    daysArray.push({
      date: new Date(year, month, i),
      otherMonth: false
    });
  }
  
  // Добавляем дни следующего месяца
  const remainingDays = 42 - daysArray.length; // 6 недель по 7 дней
  for (let i = 1; i <= remainingDays; i++) {
    daysArray.push({
      date: new Date(year, month + 1, i),
      otherMonth: true
    });
  }
  
  return daysArray;
}

function isToday(date) {
  const today = new Date();
  return date.getDate() === today.getDate() && 
         date.getMonth() === today.getMonth() && 
         date.getFullYear() === today.getFullYear();
}

function selectDay(date) {
  currentDate.value = new Date(date);
  currentView.value = 'day';
}

function selectMonth(month) {
  currentDate.value = new Date(currentDate.value.getFullYear(), month, 1);
  currentView.value = 'month';
}

// Функции для работы с событиями
function filterEventsByRoom(events) {
  if (!selectedRoom.value) return events;
  return events.filter(event => event.room === selectedRoom.value);
}

function getEventsForHour(hour) {
  const day = currentDate.value;
  const startOfDay = new Date(day.getFullYear(), day.getMonth(), day.getDate());
  const endOfDay = new Date(day.getFullYear(), day.getMonth(), day.getDate(), 23, 59, 59);
  
  const hourEvents = events.value.filter(event => {
    const eventStart = new Date(event.startTime);
    const eventEnd = new Date(event.endTime);
    
    return eventStart >= startOfDay && eventStart <= endOfDay && 
           (eventStart.getHours() === hour || 
            (eventStart.getHours() < hour && eventEnd.getHours() > hour) ||
            (eventStart.getHours() < hour && eventEnd.getHours() === hour && eventEnd.getMinutes() > 0));
  });

  return filterEventsByRoom(hourEvents);
}

function getEventsForDay(date) {
  const startOfDay = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const endOfDay = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 23, 59, 59);
  
  const dayEvents = events.value.filter(event => {
    const eventStart = new Date(event.startTime);
    const eventEnd = new Date(event.endTime);
    
    return (eventStart >= startOfDay && eventStart <= endOfDay) || 
           (eventEnd >= startOfDay && eventEnd <= endOfDay) ||
           (eventStart <= startOfDay && eventEnd >= endOfDay);
  });

  return filterEventsByRoom(dayEvents);
}

function getEventsForMonth(month) {
  const year = currentDate.value.getFullYear();
  const startOfMonth = new Date(year, month, 1);
  const endOfMonth = new Date(year, month + 1, 0, 23, 59, 59);
  
  const monthEvents = events.value.filter(event => {
    const eventStart = new Date(event.startTime);
    const eventEnd = new Date(event.endTime);
    
    return (eventStart >= startOfMonth && eventStart <= endOfMonth) || 
           (eventEnd >= startOfMonth && eventEnd <= endOfMonth) ||
           (eventStart <= startOfMonth && eventEnd >= endOfMonth);
  });

  return filterEventsByRoom(monthEvents);
}

function getEventStyle(event) {
  const eventStart = new Date(event.startTime);
  const eventEnd = new Date(event.endTime);
  
  const startHour = eventStart.getHours();
  const startMinutes = eventStart.getMinutes();
  const endHour = eventEnd.getHours();
  const endMinutes = eventEnd.getMinutes();
  
  const startPercentage = (startMinutes / 60) * 100;
  const durationHours = (endHour - startHour) + (endMinutes - startMinutes) / 60;
  const heightPercentage = durationHours * 100;
  
  return {
    top: `${startPercentage}%`,
    height: `${heightPercentage}%`,
    width: '95%'
  };
}

function getStatusClass(status) {
  switch (status) {
    case 'start': return 'status-start';
    case 'processing': return 'status-processing';
    case 'reject': return 'status-reject';
    case 'decline': return 'status-decline';
    case 'accepted': return 'status-accepted';
    default: return '';
  }
}

// Функции для работы с модальным окном
function openEventModal(event = null) {
  errorMessage.value = '';
  
  if (!isAuthenticated.value) {
    errorMessage.value = 'Необходимо войти в систему';
    return;
  }
  
  if (event) {
    // Проверяем права на редактирование
    if (!canEditEvent(event)) {
      errorMessage.value = 'У вас нет прав на редактирование этого мероприятия';
      return;
    }
    currentEvent.value = { ...event };
    isEditMode.value = true;
  } else {
    // Создание нового события
    const defaultStartTime = new Date(currentDate.value);
    defaultStartTime.setHours(defaultStartTime.getHours() + 1, 0, 0, 0);
    
    const defaultEndTime = new Date(defaultStartTime);
    defaultEndTime.setHours(defaultEndTime.getHours() + 1);
    
    currentEvent.value = {
      id: Date.now(),
      title: '',
      fullName: '',
      phone: '',
      startTime: formatDateTimeForInput(defaultStartTime),
      endTime: formatDateTimeForInput(defaultEndTime),
      eventType: 'closed',
      isCommercial: false,
      attendeesCount: '0-10',
      technicalRequirements: '',
      catering: '',
      description: '',
      status: 'start',
      comments: [],
      organizerId: currentUser.value.id,
      organizerName: currentUser.value.name,
      room: selectedRoom.value || '',
    };
    isEditMode.value = false;
  }
  
  showEventModal.value = true;
}

function closeEventModal() {
  showEventModal.value = false;
  newComment.value = '';
}

function addComment() {
  if (newComment.value.trim()) {
    currentEvent.value.comments.push({
      text: newComment.value.trim(),
      date: new Date()
    });
    newComment.value = '';
  }
}

function updateEventStatus(status) {
  currentEvent.value.status = status;
}

function checkTimeConflict(startTime, endTime, eventId, room) {
  const start = new Date(startTime);
  const end = new Date(endTime);
  
  return events.value.some(event => {
    if (event.id === eventId) return false;
    if (event.room !== room) return false; // Проверяем только события в том же помещении
    
    const eventStart = new Date(event.startTime);
    const eventEnd = new Date(event.endTime);
    
    return (start < eventEnd && end > eventStart);
  });
}

function saveEvent() {
  // Валидация
  if (!currentEvent.value.title.trim()) {
    errorMessage.value = 'Пожалуйста, введите название мероприятия';
    return;
  }
  
  if (!currentEvent.value.room) {
    errorMessage.value = 'Пожалуйста, выберите помещение';
    return;
  }
  
  if (!currentEvent.value.startTime || !currentEvent.value.endTime) {
    errorMessage.value = 'Пожалуйста, укажите время начала и окончания';
    return;
  }
  
  const startTime = new Date(currentEvent.value.startTime);
  const endTime = new Date(currentEvent.value.endTime);
  
  if (startTime >= endTime) {
    errorMessage.value = 'Время окончания должно быть позже времени начала';
    return;
  }
  
  // Проверка на конфликт времени в выбранном помещении
  if (checkTimeConflict(startTime, endTime, currentEvent.value.id, currentEvent.value.room)) {
    errorMessage.value = 'Выбранное помещение занято в указанное время';
    return;
  }
  
  if (isEditMode.value) {
    // Обновление существующего события
    const index = events.value.findIndex(e => e.id === currentEvent.value.id);
    if (index !== -1) {
      events.value[index] = { ...currentEvent.value };
    }
  } else {
    // Добавление нового события
    events.value.push({ ...currentEvent.value });
  }
  
  closeEventModal();
}

// Функции авторизации
function selectRole(role) {
  selectedRole.value = role;
}

function login() {
  if (!selectedRole.value || !userName.value.trim()) {
    authError.value = 'Пожалуйста, выберите роль и введите имя';
    return;
  }

  currentUser.value = {
    role: selectedRole.value,
    id: Date.now().toString(),
    name: userName.value.trim()
  };
  
  isAuthenticated.value = true;
  authError.value = '';
}

function logout() {
  isAuthenticated.value = false;
  selectedRole.value = '';
  userName.value = '';
  currentUser.value = {
    role: '',
    id: '',
    name: ''
  };
}

// Оставляем только функцию canEditEvent
function canEditEvent(event) {
  if (currentUser.value.role === 'admin') return true;
  return event.organizerId === currentUser.value.id;
}

// Добавляем новую функцию для обработки клика по событию
function handleEventClick(event) {
  if (!canEditEvent(event)) {
    errorMessage.value = 'У вас нет прав на редактирование этого мероприятия';
    return;
  }
  openEventModal(event);
}

// Добавляем вычисляемое свойство для проверки возможности удаления
const canDeleteEvent = computed(() => {
  if (!currentEvent.value) return false;
  if (currentUser.value.role === 'admin') return true;
  return currentEvent.value.organizerId === currentUser.value.id && 
         currentEvent.value.status === 'start';
});

// Добавляем функцию удаления события
function deleteEvent() {
  if (!canDeleteEvent.value) {
    errorMessage.value = 'У вас нет прав на удаление этого мероприятия';
    return;
  }
  
  const index = events.value.findIndex(e => e.id === currentEvent.value.id);
  if (index !== -1) {
    events.value.splice(index, 1);
  }
  
  closeEventModal();
}

// Добавляем функцию принятия записи
function acceptEvent() {
  if (currentUser.value.role !== 'admin') {
    errorMessage.value = 'Только администратор может принимать записи';
    return;
  }
  
  currentEvent.value.status = 'accepted';
}
</script>

<style>
:root {
  --primary-color: #4a6fa5;
  --primary-light: #e1ebf7;
  --secondary-color: #6c757d;
  --success-color: #28a745;
  --warning-color: #ffc107;
  --danger-color: #dc3545;
  --info-color: #17a2b8;
  --light-color: #f8f9fa;
  --dark-color: #343a40;
  --border-color: #dee2e6;
  --shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  
  --status-start-color: #17a2b8;
  --status-processing-color: #ffc107;
  --status-reject-color: #dc3545;
  --status-decline-color: #6c757d;
  --status-accepted-color: #28a745;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;

}

body {
  font-family: 'Roboto', 'Arial', sans-serif;
  line-height: 1.6;
  background-color: #f5f5f5;
}

.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

/* Заголовок и фильтры */
header {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
}

h1 {
  color: var(--primary-color);
  margin-bottom: 10px;
}

.calendar-filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.button-group {
  display: flex;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.button-group button {
  padding: 8px 15px;
  background-color: white;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s;
}

.button-group button.active {
  background-color: var(--primary-color);
  color: white;
}

.date-selector {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: bold;
}

.date-selector button {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--primary-color);
}

.create-event-btn {
  padding: 10px 20px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  align-self: flex-end;
  transition: background-color 0.2s;
}

.create-event-btn:hover {
  background-color: #3a5a8c;
}

/* Дневной вид */
.day-view {
  background-color: white;
  border-radius: 8px;
  box-shadow: var(--shadow);
  overflow: hidden;
}

.time-slots {
  display: flex;
  flex-direction: column;
}

.time-slot {
  display: flex;
  min-height: 60px;
  border-bottom: 1px solid var(--border-color);
  position: relative;
}

.time-label {
  width: 60px;
  padding: 5px;
  text-align: center;
  font-size: 12px;
  color: var(--secondary-color);
  border-right: 1px solid var(--border-color);
}

.time-content {
  flex: 1;
  position: relative;
  padding: 2px;
}

.event-card {
  position: absolute;
  left: 5px;
  border-radius: 4px;
  padding: 5px;
  font-size: 12px;
  overflow: hidden;
  cursor: pointer;
  box-shadow: var(--shadow);
  transition: transform 0.2s;
  z-index: 1;
}

.event-card:hover {
  transform: scale(1.02);
  z-index: 2;
}

.event-time {
  font-weight: bold;
  margin-bottom: 3px;
}

.event-title {
  font-weight: bold;
  margin-bottom: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.event-room {
  font-size: 11px;
}

/* Месячный вид */
.month-view {
  background-color: white;
  border-radius: 8px;
  box-shadow: var(--shadow);
  overflow: hidden;
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background-color: var(--primary-light);
  border-bottom: 1px solid var(--border-color);
}

.weekday {
  padding: 10px;
  text-align: center;
  font-weight: bold;
}

.month-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-auto-rows: minmax(100px, auto);
}

.day-cell {
  border-right: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
  padding: 5px;
  position: relative;
  cursor: pointer;
  transition: background-color 0.2s;
}

.day-cell:hover {
  background-color: var(--primary-light);
}

.day-cell.other-month {
  background-color: #f9f9f9;
  color: var(--secondary-color);
}

.day-cell.today {
  background-color: var(--primary-light);
  font-weight: bold;
}

.day-number {
  font-size: 14px;
  margin-bottom: 5px;
}

.day-events {
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
  max-height: 80px;
}

.month-event-indicator {
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Годовой вид */
.year-view {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

.year-month {
  background-color: white;
  border-radius: 8px;
  padding: 10px;
  box-shadow: var(--shadow);
  cursor: pointer;
  transition: transform 0.2s;
}

.year-month:hover {
  transform: scale(1.03);
}

.year-month h3 {
  text-align: center;
  margin-bottom: 10px;
  color: var(--primary-color);
}

.month-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  justify-content: center;
}

.year-event-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

/* Статусы событий */
.status-start {
  background-color: var(--status-start-color);
  color: white;
  border-left: 3px solid #0f7a8a;
}

.status-processing {
  background-color: var(--status-processing-color);
  color: #333;
  border-left: 3px solid #d6a206;
}

.status-reject {
  background-color: var(--status-reject-color);
  color: white;
  border-left: 3px solid #b02a37;
}

.status-decline {
  background-color: var(--status-decline-color);
  color: white;
  border-left: 3px solid #565e64;
}

.status-accepted {
  background-color: var(--status-accepted-color);
  color: white;
  border-left: 3px solid #1e7e34;
}

/* Модальное окно */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  color: #000 !important;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.modal-content h2 {
  margin-bottom: 20px;
  color: var(--primary-color);
}

.form-group {
  margin-bottom: 15px;
}

.form-row {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
}

.form-row .form-group {
  flex: 1;
  margin-bottom: 0;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

input, textarea, select {
  width: 100%;
  padding: 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-family: inherit;
}

textarea {
  min-height: 80px;
  resize: vertical;
}

.comments-section {
  margin-top: 20px;
  border-top: 1px solid var(--border-color);
  padding-top: 15px;
}

.comments-list {
  max-height: 200px;
  overflow-y: auto;
  margin-bottom: 15px;
}

.comment {
  background-color: #f9f9f9;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 10px;
}

.comment-text {
  margin-bottom: 5px;
}

.comment-date {
  font-size: 12px;
  color: var(--secondary-color);
  text-align: right;
}

.add-comment {
  display: flex;
  gap: 10px;
}

.add-comment textarea {
  flex: 1;
  min-height: 60px;
}

.add-comment button {
  align-self: flex-end;
  padding: 8px 15px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.error-message {
  color: var(--danger-color);
  margin: 10px 0;
  font-weight: bold;
}

.modal-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  gap: 10px;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.close-btn {
  padding: 10px 15px;
  background-color: var(--secondary-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.delete-btn {
  padding: 10px 15px;
  background-color: var(--danger-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.accept-btn {
  padding: 10px 15px;
  background-color: var(--success-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.accept-btn:disabled {
  background-color: var(--secondary-color);
  cursor: not-allowed;
  opacity: 0.7;
}
.save-btn {
  padding: 10px 15px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}
.save-btn:disabled {
  background-color: var(--secondary-color);
  cursor: not-allowed;
  opacity: 0.7;
}

/* Стили для выбора помещения */
.room-filter {
  display: flex;
  align-items: center;
  gap: 10px;
}

.room-select {
  width: 100%;
  padding: 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background-color: white;
  cursor: pointer;
}

.room-select:focus {
  outline: none;
  border-color: var(--primary-color);
}

/* Адаптивный дизайн */
@media (max-width: 768px) {
  .calendar-filters {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .form-row {
    flex-direction: column;
    gap: 15px;
  }
  
  .year-view {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .modal-content {
    width: 95%;
    padding: 15px;
  }
  
  .modal-actions {
    flex-direction: column;
    gap: 10px;
  }
  
  .status-actions {
    order: -1;
    margin-bottom: 10px;
  }
}

@media (max-width: 480px) {
  .year-view {
    grid-template-columns: 1fr;
  }
  
  .weekdays, .month-grid {
    font-size: 12px;
  }
  
  .day-cell {
    min-height: 80px;
  }
}

/* Добавляем стили для новых элементов формы */
.radio-group {
  display: flex;
  gap: 15px;
  margin-top: 5px;
}

.radio-label, .checkbox-label {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
}

.radio-label input[type="radio"],
.checkbox-label input[type="checkbox"] {
  width: auto;
  margin-right: 5px;
}

/* Добавляем стили для экрана авторизации */
.auth-screen {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.auth-form {
  background-color: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: var(--shadow);
  width: 100%;
  max-width: 400px;
}

.auth-form h2 {
  text-align: center;
  margin-bottom: 1.5rem;
  color: var(--primary-color);
}

.role-selector {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
}

.role-selector button {
  flex: 1;
  padding: 0.75rem;
  border: 2px solid var(--primary-color);
  border-radius: 4px;
  background-color: white;
  color: var(--primary-color);
  cursor: pointer;
  transition: all 0.2s;
}

.role-selector button.active {
  background-color: var(--primary-color);
  color: white;
}

.login-btn {
  width: 100%;
  padding: 0.75rem;
  margin-top: 1rem;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.login-btn:disabled {
  background-color: var(--secondary-color);
  cursor: not-allowed;
}

.user-info {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.logout-btn {
  padding: 0.5rem 1rem;
  background-color: var(--secondary-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

/* Добавляем стили для нередактируемых событий */
.event-card.not-editable {
  opacity: 0.7;
  cursor: not-allowed;
}

.event-card.not-editable:hover {
  transform: none;
}

.month-event-indicator.not-editable {
  opacity: 0.7;
  cursor: not-allowed;
}

.event-organizer {
  font-size: 11px;
  color: var(--secondary-color);
  margin-top: 2px;
}
</style>