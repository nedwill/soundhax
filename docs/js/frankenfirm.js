/* http://stackoverflow.com/a/5077091 */
String.prototype.format = function () {
  var args = arguments;
  return this.replace(/\{(\d+)\}/g, function (m, n) { return args[n]; });
};

var ERR_INVALID_INPUT = 0;
var ERR_NOT_SUPPORTED = 1;
var ERR_USE_NORMAL_FIRST = 2;
var ERR_LIKELY_WRONG_NORMAL = 3;

var ERRS_USE_NORMAL = [ERR_USE_NORMAL_FIRST, ERR_LIKELY_WRONG_NORMAL];

function checkDownloadable() {
  var href = checkSelection();
  console.log("check result", href)
  if (ERRS_USE_NORMAL.includes(href)) {
    $('#download').text("Normal Soundhax");
  } else if (href === ERR_INVALID_INPUT) {
    $('#download').text("Invalid Input");
  } else if (href === ERR_NOT_SUPPORTED) {
    $('#download').text("Not Supported");
  } else {
    $('#download').text("Download M4A");
  }
  if (typeof href === "string" || ERRS_USE_NORMAL.includes(href)) {
    $('#download').addClass('active');
  } else {
    $('#download').removeClass('active');
  }
}

$('button.group').on('click', function() {
  if ($(this).parent().hasClass('forced')) {
    return;
  }
  if ($(this).hasClass('selected')) {
    $(this).removeClass('selected');
  } else {
    $(this).siblings().removeClass('selected');
    $(this).addClass('selected');
  }

  checkDownloadable();
});

$('select').on('change', function() {
  checkDownloadable();
});

function regionFN(region) {
  switch (region) {
    case "E":
      return "eur";
    case "U":
      return "usa";
    case "J":
      return "jpn";
    case "K":
      return "kor";
    case "C":
      return "chn";
    case "T":
      return "twn";
  }
}

function updateConsoleSelector(region, show) {
  if (["C", "T"].includes(region)) {
    show = false;
  }
  if (show) {
    $('.console').show();
  } else {
    $('.console').hide();
    if (!$('.console').hasClass("forced")) {
      $('.console').children().removeClass('selected');
    }
  }
}

function checkSelection() {
  // Possible max minor for each major, major as key
  var major_minor_map = {
    0: -1, // invalidate all 0.x
    1: 1,
    2: 2,
    3: 1,
    4: 5,
    5: 1,
    6: 4,
    7: 2,
    8: 1,
    9: 9,
    10: 7,
    11: 17
  };

  var error = $('.error').children('.selected').attr('id');
  var console_ = $('.console').children('.selected').attr('id');
  var major = parseInt($('#major').val());
  var minor = parseInt($('#minor').val());
  var nver = parseInt($('#nver').val());
  var region = $('#region').val();

  updateConsoleSelector(region, major >= 8);

  if (major == 11 && minor == 17 && ["K", "C", "T"].includes(region)) {
    return ERR_INVALID_INPUT;
  }

  var minor_max = major_minor_map[major];
  if (!isNaN(minor_max) && minor > minor_max) {
    return ERR_INVALID_INPUT;
  }

  if (console_ === "n3ds") {
    return ERR_USE_NORMAL_FIRST;
  }

  if (["K", "C", "T"].includes(region)) {
    return ERR_USE_NORMAL_FIRST;
  }

  switch (nver) {
    case 0:
    case 1:
    case 2:
    case 3:
      console.log("nver 0-3")
      if (major < 2 || (major == 2 && minor <= 1)) {
        switch (error) {
          case "unplayable":
            // very unlikely to have v1027 sound app in this case?
            return "soundhax-{0}-{1}.m4a".format(regionFN(region), "o3ds-pre2.1");
          case "crash":
            return ERR_INVALID_INPUT; // WTF
          default:
            return ERR_USE_NORMAL_FIRST;
        }
      } else if (major < 5) {
        switch (error) {
          case "unplayable":
            return "soundhax-{0}-{1}.m4a".format(regionFN(region), "o3ds-pre2.1");
          case "crash":
            return "soundhax-{0}-{1}.m4a".format(regionFN(region), "o3ds-v2.1and2.2");
          default:
            return ERR_USE_NORMAL_FIRST;
        }
      } else if (major < 11 || (major == 11 && minor <= 3)) {
        switch (error) {
          case "unplayable":
            return "soundhax-{0}-{1}.m4a".format(regionFN(region), "o3ds-pre2.1-post5franken");
          case "crash":
            return "soundhax-{0}-{1}.m4a".format(regionFN(region), "o3ds-v2.1and2.2-post5franken");
          default:
            return ERR_USE_NORMAL_FIRST;
        }
      } else if ((major == 11 && minor > 3) || major > 11) {
          return ERR_NOT_SUPPORTED;
      }
    case 4:
      console.log("nver 4")
      if (major < 2 || (major == 2 && minor < 1)) {
        return ERR_INVALID_INPUT; // WTF
      } else if (major == 2 && minor == 1) {
        switch (error) {
          case "unplayable":
            return "soundhax-{0}-{1}.m4a".format(regionFN(region), "o3ds-v2.1and2.2");
          case "crash":
            return ERR_INVALID_INPUT; // WTF
          default:
            return ERR_USE_NORMAL_FIRST;
        }
      } else if (major < 5) {
        switch (error) {
          case "unplayable":
            return ERR_LIKELY_WRONG_NORMAL;
          case "crash":
            return "soundhax-{0}-{1}.m4a".format(regionFN(region), "o3ds-v2.1and2.2");
          default:
            return ERR_USE_NORMAL_FIRST;
        }
      } else if (major < 11 || (major == 11 && minor <= 3)) {
        switch (error) {
          case "unplayable":
            return ERR_LIKELY_WRONG_NORMAL;
          case "crash":
            return "soundhax-{0}-{1}.m4a".format(regionFN(region), "o3ds-v2.1and2.2-post5franken");
          default:
            return ERR_USE_NORMAL_FIRST;
        }
      } else if ((major == 11 && minor > 3) || major > 11) {
          return ERR_NOT_SUPPORTED;
      }
    case 5:
    case 6:
    case 7:
    case 8:
    case 9:
    case 10:
      console.log("nver 5-10");
      if (major < 5) {
        switch (error) {
          case "unplayable":
          case "crash":
            return ERR_LIKELY_WRONG_NORMAL;
          default:
            return ERR_USE_NORMAL_FIRST;
        }
      } else if (major < 11 || (major == 11 && minor <= 3)) {
        switch (error) {
          case "unplayable":
          case "crash":
            return ERR_LIKELY_WRONG_NORMAL;
          default:
            return ERR_USE_NORMAL_FIRST;
        }
      } else if ((major == 11 && minor > 3) || major > 11) {
          return ERR_NOT_SUPPORTED;
      }
    default:
      if (nver < 37) {
        console.log("nver 11-36");
        switch (error) {
          case "unplayable":
          case "crash":
            return ERR_NOT_SUPPORTED;
          default:
            return "soundhax-{0}-{1}.m4a".format(regionFN(region), "o3ds-post5.0");
        }
      } else {
        console.log("nver 37+");
        return ERR_NOT_SUPPORTED;
      }
  }
}
checkDownloadable();

$('#download').on('click', function() {
  if (!$(this).hasClass('active')) {
    return;
  }

  var href = checkSelection();
  if (ERRS_USE_NORMAL.includes(href)) {
    if (href === ERR_LIKELY_WRONG_NORMAL) {
      alert("You likely chosed wrong file previously in normal soundhax, make sure you select it correctly and try again.");
    }
    //window.location.href = "index.html";
    window.location.href = "http://soundhax.com";
  } else if (typeof href === "string") {
    var base = "https://github.com/danny8376/soundhax/raw/frankenfirmware/";
    window.location.href = base + href;
  }
});

function forceOptionSelected(id) {
  $('#' + id).trigger("click");
  $('#' + id).parent().addClass("forced");
  //$('#' + id).parent().hide();
}

$.each(["unplayable", "crash"], function(idx, opt) {
  if (location.search.includes(opt)) {
    forceOptionSelected(opt);
  }
});
