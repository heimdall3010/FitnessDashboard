import { accordion } from './accordion.js';
import { exportButtons } from './exportButtons.js';
import { nav } from './nav.js';
import { hamburger } from './hamburger.js';

document.addEventListener('DOMContentLoaded', () => {
  accordion();
  exportButtons();
  nav();
  hamburger();
});
