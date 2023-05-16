const handleClickOnTag = (element: Element, addedWords: string[]) => {
  const tag = element.innerHTML;

  addedWords = addedWords.filter(el => el != tag);

  element.remove();
  const multipleInput: any = document.querySelector('.multiple-input');
  multipleInput.value = tag;

  // prettier-ignore
  const tagsToSubmitInput: HTMLInputElement = document.querySelector('.tags-to-submit');
  tagsToSubmitInput.value = addedWords.join();

  return addedWords;
};

export function initMultipleInput() {
  const settingsForm = document.querySelector('.settings-form');
  settingsForm.addEventListener('keypress', (e: any) => {
    if (e.keyCode === 13) {
      e.preventDefault();
    }
  });

  // prettier-ignore
  const tagsToSubmitInput: HTMLInputElement = document.querySelector('.tags-to-submit');
  const multipleInput: any = document.querySelector('.multiple-input');

  const wordsBlock: HTMLDivElement = document.querySelector(
    '.multiple-input-items',
  );
  const wordDivs = wordsBlock.querySelectorAll('.multiple-input-word');
  let addedWords: string[] = [];
  wordDivs.forEach(el => {
    addedWords.push(el.innerHTML);
    el.addEventListener('click', () => {
      addedWords = handleClickOnTag(el, addedWords);
    });
  });

  tagsToSubmitInput.value = addedWords.join();

  multipleInput.addEventListener('input', () => {
    let inputValue = multipleInput.value.trim();
    if (inputValue.length > 32) {
      multipleInput.value = inputValue.slice(0, 32);
      return;
    }
  });

  multipleInput.addEventListener('keyup', (event: any) => {
    if (event.keyCode === 13 || event.keyCode === 188) {
      if (!multipleInput.value) {
        return;
      }
      let inputValue = multipleInput.value.trim();
      if (!inputValue) {
        return;
      } else if (inputValue.length > 32) {
        multipleInput.value = inputValue.slice(0, 32);
        return;
      }

      // prettier-ignore
      inputValue = inputValue.charAt(0).toUpperCase() + inputValue.substr(1).toLowerCase();
      if (
        inputValue.substring(inputValue.length - 1, inputValue.length) == ','
      ) {
        inputValue = inputValue.substring(0, inputValue.length - 1);
        event.target.value = inputValue;
      }
      inputValue = inputValue.replaceAll(',', '');

      if (addedWords.includes(inputValue)) {
        return;
      }

      const wordDiv = document.createElement('div');
      // prettier-ignore
      wordDiv.className = 'cursor-pointer multiple-input-word bg-sky-300 hover:bg-sky-400 dark:bg-sky-500 dark:hover:bg-sky-600 rounded text-center py-1/2 px-2';
      wordDiv.innerHTML = inputValue;
      addedWords.push(inputValue);
      wordDiv.addEventListener('click', () => {
        addedWords = handleClickOnTag(wordDiv, addedWords);
      });

      wordsBlock.appendChild(wordDiv);
      multipleInput.value = '';
      tagsToSubmitInput.value = addedWords.join();
    }

    // Edit last tag on click "backspace"
    // Will be removed after demo
    // TODO Remove after demo
    // else if (event.keyCode === 8 && multipleInput.value.length === 0) {
    //   const addedWordsDivs = document.querySelectorAll('.multiple-input-word');
    //   const lastAdded = addedWordsDivs[addedWordsDivs.length - 1];
    //   if (!lastAdded) {
    //     return;
    //   }
    //   const word = lastAdded.innerHTML;
    //   if (word || word != '') {
    //     multipleInput.value = word;
    //     lastAdded.remove();

    //     addedWords.slice(0, addedWords.length - 1);
    //     tagsToSubmitInput.value = addedWords.join();
    //   }
    // }
  });
}