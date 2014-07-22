$(function() {

   var time = $('.time');
   var cbox = $('#showHideTime');
   
   function showHideTime() {
      if (cbox[0].checked) {
         time.hide();
      }
      else {
         time.show();
      }
   }

   showHideTime();
   cbox.click(showHideTime);

});
