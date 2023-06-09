import {Modal} from 'flowbite';
import type {ModalOptions, ModalInterface} from 'flowbite';
import debounce = require('lodash.debounce');

const currentSearchInput: HTMLInputElement =
  document.querySelector('#mainSearchInput');
const searchDiv: HTMLElement = document.querySelector('#quickSearchModal');

const modalOptions: ModalOptions = {
  backdrop: 'dynamic',
  closable: true,
  onHide: () => {},
  onShow: () => {
    const modalBack = document.querySelector('.bg-opacity-50');
    modalBack.addEventListener('click', () => {
      currentSearchInput.value = '';
      quickSearchModal.hide();
    });
  },
  onToggle: () => {},
};

const quickSearchModal: ModalInterface = new Modal(searchDiv, modalOptions);

export function quickSearch() {
  if (currentSearchInput && searchDiv) {
    currentSearchInput.addEventListener('input', debounce(onInputChange, 500));
    currentSearchInput.addEventListener('keypress', async e => {
      if (e.key === 'Enter') {
        const urlParams = new URLSearchParams({
          q: currentSearchInput.value.toLowerCase(),
        });
        const res = await fetch('/search_interpretations?' + urlParams);
        if (res.status === 200) {
          window.location.replace(res.url);
        } else {
          return;
        }
      }
    });
  }
}

const onInputChange = async (e: any) => {
  e.preventDefault();
  if (currentSearchInput.value.length > 0) {
    const urlParams = new URLSearchParams({
      search_query: currentSearchInput.value.toLowerCase(),
    });
    const res = await fetch('/quick_search?' + urlParams);
    const json = await res.json();
    if (res.status === 200) {
      let emptyEntityArr = [];

      for (const entity in json) {
        // iterate over json from back end
        const el: HTMLDivElement = document.querySelector(
          `#quickSearchBlock-${entity}`,
        );
        const secondUnusedLink = document.querySelector(`.${entity}Text-1`);
        const emptySearchDiv = document.querySelector('#emptyQuickSearchDiv');
        if (secondUnusedLink) {
          secondUnusedLink.classList.remove('hidden');
        }
        if (json[entity].length < 1) {
          emptyEntityArr.push(entity);
          if (el) {
            el.classList.add('hidden');
          }
        }
        if (json[entity].length == 1) {
          if (secondUnusedLink) {
            secondUnusedLink.classList.add('hidden');
          }
        }
        if (emptyEntityArr.length === 4) {
          emptySearchDiv.classList.remove('hidden');
        }

        for (const obj in json[entity]) {
          // iterate over every entity in json
          el.classList.remove('hidden');
          emptySearchDiv.classList.add('hidden');
          const link = document.querySelector(`#${entity}Text-${obj}`);
          // taking needed html element for markup
          if (link) {
            // setting needed values to element
            link.textContent = json[entity][obj].label;
            link.setAttribute('href', json[entity][obj].url);
          }
        }
      }
      quickSearchModal.show();
    } else {
      return;
    }
  }
};
