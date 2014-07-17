$(function() {

   $(document).on('click', 'tr.entry', function(event) {
      var theRow = $(event.target).closest('tr.entry');
      var theCell = theRow.children('td:last-child');

      var time = theCell.find('.time');
      if (time.size()) {
         time.remove();
      }
      else {
         time = $('<div class=time></div>').text(theRow.attr('data-time'));
         theCell.append(time);
      }
      event.stopPropagation();
   });

});
