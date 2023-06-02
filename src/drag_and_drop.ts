// Default SortableJS
import Sortable from 'sortablejs';

export function initDnD() {
  const divsForSectionsDnD: NodeListOf<HTMLDivElement> =
    document.querySelectorAll('#draggableSectionItems');
  const divsForSubCollectionsDnD: NodeListOf<HTMLDivElement> =
    document.querySelectorAll('[data-dnd="dnd-sub-collection"]');
  const divsAreEmpty = document.querySelectorAll('#empty-dnd-entity');
  divsForSubCollectionsDnD.forEach((div: HTMLDivElement) =>
    Sortable.create(div, {
      group: {
        name: 'sub_collections',
        pull: true,
        put: ['sub_collections'],
      },
      animation: 100,
      onEnd: function (/**Event*/ evt) {
        var itemEl = evt.item; // dragged HTMLElement
        console.log(
          'we moved',
          itemEl.getAttribute('data-entity-type'),
          itemEl.getAttribute('data-entity-id'),
        );
        evt.to; // target list
        evt.from; // previous list
        console.log(
          'from',
          evt.from.getAttribute('data-entity-type'),
          evt.from.getAttribute('data-entity-id'),
        );
        console.log(
          'to',
          evt.to.getAttribute('data-entity-type'),
          evt.to.getAttribute('data-entity-id'),
        );

        console.log('evt.oldIndex', evt.oldIndex);
        evt.oldIndex; // element's old index within old parent
        console.log('evt.newIndex', evt.newIndex);
        evt.newIndex; // element's new index within new parent
        console.log('evt.oldDraggableIndex', evt.oldDraggableIndex);
        evt.oldDraggableIndex; // element's old index within old parent, only counting draggable elements
        console.log('evt.newDraggableIndex', evt.newDraggableIndex);
        evt.newDraggableIndex; // element's new index within new parent, only counting draggable elements
        evt.clone; // the clone element
        evt.pullMode; // when item is in another sortable: `"clone"` if cloning, `true` if moving
      },
    }),
  );
  divsForSectionsDnD.forEach((div: HTMLDivElement) =>
    Sortable.create(div, {
      group: {
        name: 'sections',
        pull: true,
        put: ['sections'],
      },
      animation: 100,
      onEnd: function (/**Event*/ evt) {
        var itemEl = evt.item; // dragged HTMLElement
        console.log(
          'we moved',
          itemEl.getAttribute('data-entity-type'),
          itemEl.getAttribute('data-entity-id'),
        );
        evt.to; // target list
        evt.from; // previous list
        console.log(
          'from',
          evt.from.getAttribute('data-entity-type'),
          evt.from.getAttribute('data-entity-id'),
        );
        console.log(
          'to',
          evt.to.getAttribute('data-entity-type'),
          evt.to.getAttribute('data-entity-id'),
        );

        console.log('evt.oldIndex', evt.oldIndex);
        evt.oldIndex; // element's old index within old parent
        console.log('evt.newIndex', evt.newIndex);
        evt.newIndex; // element's new index within new parent
        console.log('evt.oldDraggableIndex', evt.oldDraggableIndex);
        evt.oldDraggableIndex; // element's old index within old parent, only counting draggable elements
        console.log('evt.newDraggableIndex', evt.newDraggableIndex);
        evt.newDraggableIndex; // element's new index within new parent, only counting draggable elements
        evt.clone; // the clone element
        evt.pullMode; // when item is in another sortable: `"clone"` if cloning, `true` if moving
      },
    }),
  );
  divsForSubCollectionsDnD.forEach((div: HTMLDivElement) =>
    Sortable.create(div, {
      group: {
        name: 'sub_collections',
        pull: true,
        put: ['sub_collections'],
      },
      animation: 100,
      onEnd: function (/**Event*/ evt) {
        var itemEl = evt.item; // dragged HTMLElement
        console.log(
          'we moved',
          itemEl.getAttribute('data-entity-type'),
          itemEl.getAttribute('data-entity-id'),
        );
        evt.to; // target list
        evt.from; // previous list
        console.log(
          'from',
          evt.from.getAttribute('data-entity-type'),
          evt.from.getAttribute('data-entity-id'),
        );
        console.log(
          'to',
          evt.to.getAttribute('data-entity-type'),
          evt.to.getAttribute('data-entity-id'),
        );

        console.log('evt.oldIndex', evt.oldIndex);
        evt.oldIndex; // element's old index within old parent
        console.log('evt.newIndex', evt.newIndex);
        evt.newIndex; // element's new index within new parent
        console.log('evt.oldDraggableIndex', evt.oldDraggableIndex);
        evt.oldDraggableIndex; // element's old index within old parent, only counting draggable elements
        console.log('evt.newDraggableIndex', evt.newDraggableIndex);
        evt.newDraggableIndex; // element's new index within new parent, only counting draggable elements
        evt.clone; // the clone element
        evt.pullMode; // when item is in another sortable: `"clone"` if cloning, `true` if moving
      },
    }),
  );
  divsAreEmpty.forEach((div: HTMLDivElement) =>
    Sortable.create(div, {
      group: {
        name: 'empty',
        pull: false,
        put: ['sections', 'sub_collections'],
      },
      animation: 100,
      onEnd: function (/**Event*/ evt) {
        var itemEl = evt.item; // dragged HTMLElement
        console.log(
          'we moved',
          itemEl.getAttribute('data-entity-type'),
          itemEl.getAttribute('data-entity-id'),
        );
        evt.to; // target list
        evt.from; // previous list
        console.log(
          'from',
          evt.from.getAttribute('data-entity-type'),
          evt.from.getAttribute('data-entity-id'),
        );
        console.log(
          'to',
          evt.to.getAttribute('data-entity-type'),
          evt.to.getAttribute('data-entity-id'),
        );

        console.log('evt.oldIndex', evt.oldIndex);
        evt.oldIndex; // element's old index within old parent
        console.log('evt.newIndex', evt.newIndex);
        evt.newIndex; // element's new index within new parent
        console.log('evt.oldDraggableIndex', evt.oldDraggableIndex);
        evt.oldDraggableIndex; // element's old index within old parent, only counting draggable elements
        console.log('evt.newDraggableIndex', evt.newDraggableIndex);
        evt.newDraggableIndex; // element's new index within new parent, only counting draggable elements
        evt.clone; // the clone element
        evt.pullMode; // when item is in another sortable: `"clone"` if cloning, `true` if moving
      },
    }),
  );
}
