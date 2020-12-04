/* http://stackoverflow.com/a/5077091 */
String.prototype.format = function () {
  var args = arguments;
  return this.replace(/\{(\d+)\}/g, function (m, n) { return args[n]; });
};

$('button.group').on('click', function() {
  if ($(this).hasClass('selected')) {
    $(this).removeClass('selected');
  } else {
    $(this).siblings().removeClass('selected');
    $(this).addClass('selected');
  }

  // There is no CHN/TWN N3DS
  if ($('.region .no_n3ds').hasClass('selected')) {
    $('#n3ds').removeClass('selected');
    $('#n3ds').hide();
  } else {
    $('#n3ds').show();
  }

  // Hide/show relevant system versions
  $('.firmware .group').each(function (index, elem) {
    var hide_n3ds = $(elem).hasClass('no_n3ds') && $('#n3ds').hasClass('selected');
    var hide_kct = $(elem).hasClass('no_kct') && $('.kct').hasClass('selected');
    if (hide_n3ds || hide_kct) {
      $(elem).removeClass('selected');
      $(elem).hide();
    } else {
      $(elem).show();
    }
  })

  if (   $('.region').children().hasClass('selected')
      && $('.console').children().hasClass('selected')
      && $('.firmware').children().hasClass('selected')
  ) {
    $('#download').addClass('active');
  } else {
    $('#download').removeClass('active');
  }

});

$('#download').on('click', function() {
  if (!$(this).hasClass('active')) {
    return;
  }

  var region = $('.region').children('.selected').attr('id');
  var console_ = $('.console').children('.selected').attr('id');
  var firmware_ = $('.firmware').children('.selected').attr('id');

  var base = "https://github.com/nedwill/soundhax/raw/master/";
  if(console_ == 'n3ds')
    var filename = "soundhax-{0}-{1}.m4a".format(region, console_);
  else
    var filename = "soundhax-{0}-{1}-{2}.m4a".format(region, console_, firmware_);
  window.location.href = base + filename;
});
