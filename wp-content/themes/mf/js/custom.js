/*-----------------------------------------------------------------------------------*/
/*	PRELOADER
/*-----------------------------------------------------------------------------------*/
jQuery(window).load(function() { // makes sure the whole site is loaded
	jQuery("#status").fadeOut(); // will first fade out the loading animation
	jQuery("#preloader").delay(350).fadeOut("slow"); // will fade out the white DIV that covers the website.
});
/*-----------------------------------------------------------------------------------*/
/*	IMAGE HOVER
/*-----------------------------------------------------------------------------------*/
jQuery(document).ready(function($){
 
	 $('.title-wrap, .subtitle-wrap, .portfolio-link-wrap').each(function() {
        $(this).data('wrapping', $(this).width());
        $(this).css('width', 0);
      });

      $('div.images').bind('mouseenter', function() {
        $(this).find('.title-wrap').stop().each(function() {
          $(this).animate({
            width: $(this).data('wrapping')
          }, 400);
        });

        $(this).find('.subtitle-wrap').stop().each(function() {
          $(this).delay(200).animate({
            width: $(this).data('wrapping')
          }, 400);
        });
        
        $(this).find('.portfolio-link-wrap').stop().each(function() {
          $(this).delay(400).animate({
            width: $(this).data('wrapping')
          }, 400);
        });
      });

      $('div.images').bind('mouseleave', function() {
        $(this).delay(400).find('.title-wrap').stop().each(function() {
          $(this).animate({
            width: 0
          }, 400);
        });

        $(this).delay(200).find('.subtitle-wrap').stop().each(function() {
          $(this).animate({
            width: 0
          }, 400);
        });
        
        $(this).find('.portfolio-link-wrap').stop().each(function() {
          $(this).animate({
            width: 0
          }, 400);
        });
      });
      
});
/*-----------------------------------------------------------------------------------*/
/*	FANCYBOX
/*-----------------------------------------------------------------------------------*/
jQuery(document).ready(function() {

	// initiate fancybox for images
	jQuery("a.popup, a[rel=group]").fancybox({
				closeClick : true,
				 helpers : {
            overlay : {
                locked : false
            }
        }     
		});
	
	
	// initiate fancybox for videos
	jQuery(".video-popup").fancybox({
				'width'				: '70%',
				'height'			: '80%',
				'autoScale'			: false,
				'type'				: 'iframe',
				closeClick : true,
				 helpers : {
            overlay : {
                locked : false
            }
        }     
			});

});
/*-----------------------------------------------------------------------------------*/
/*	FLEXSLIDER
/*-----------------------------------------------------------------------------------*/
jQuery(document).ready(function(){
	if ( jQuery('.flexslider')[0] ) {
	    jQuery('.flexslider').flexslider({
	    	animation: "slide"
	    });
	}
 });
 /*-----------------------------------------------------------------------------------*/
 /*	CONTACT FORM
 /*-----------------------------------------------------------------------------------*/
 jQuery(document).ready(function($){
 
	 $('#contactform').submit(function(){
	 
	 var action = $(this).attr('action');
	 
	 $("#message").slideUp(750,function() {
	 $('#message').hide();
	 
	 $('#submit').attr('disabled','disabled');
	 
	 $.post(action, {
	 name: $('#name').val(),
	 email: $('#email').val(),
	 comments: $('#comments').val(),
	 check: $('#check').val()
	 },
	 function(data){
	 document.getElementById('message').innerHTML = data;
	 $('#message').slideDown('slow');
	 $('#contactform img.loader').fadeOut('slow',function(){$(this).remove()});
	 $('#submit').removeAttr('disabled');
	 jQuery('#message').has('.error_message').mousemove(function() {
	 jQuery(this).hide();
	 });
	 jQuery('#message').has('#success_page').hover(function() {
	 jQuery(this).show();
	 });
	 jQuery('#message').has('#success_page').mousemove(function() {
	 jQuery(this).show();
	 });
	 
	 }
	 );
	 
	 });
	 
	 return false;
	 
	 });
 
 });
/*-----------------------------------------------------------------------------------*/
/*	RESPONSIVE NAV
/*-----------------------------------------------------------------------------------*/
jQuery(document).ready(function($){
	
	jQuery('#nav-button').click(function() {
	if( jQuery('#options').is(':visible') ){
		jQuery('#options').hide();
	} else {
		jQuery('#options').show();
	}
	});
	
	if ( jQuery(window).width() < 959) {
	jQuery('#options li a').click(function() {
			jQuery('#options').hide();
	});
	}
	
	jQuery(window).resize(function() {
  if ( jQuery(window).width() < 959) {
	jQuery('#options li a').click(function() {
			jQuery('#options').hide();
			jQuery('#nav-button').removeClass('nav-show');
	});
	}
	});
	
	jQuery(window).resize(function() {
  if ( jQuery(window).width() > 959) {
			jQuery('#options').show();
			jQuery('#options li a').click(function() {
			jQuery('#options').show();
	});
	}
	});
	
	$('#search-icon').click(function(){
		if ( $('#searchform').is(':visible') ) {
			$('#filters').fadeTo(300, 1).css("pointer-events","all");
			$('#options #searchform').fadeOut(300);
		} else {
			$('#filters').fadeTo(300, 0).css("pointer-events","none");
			$('#options #searchform').fadeIn(300).css("display","inline-block");
		}
	});
	
});	

jQuery.fn.slideFadeToggle  = function(speed, easing, callback) {
        return this.animate({opacity: 'toggle', height: 'toggle'}, speed, easing, callback);
};

jQuery(document).ready(function($) {	

if( $(window).width() > 960 ){	
$("ul#filters").addClass('desktop').removeClass('mobile');
$("ul#filters.desktop").on('mouseenter', 'li', function() {
			var $this    = $(this),
				$subMenu = $this.children('ul');
			if( $subMenu.length ) $this.addClass('hover');
			$subMenu.hide().stop(true, true).slideFadeToggle(200);
		}).on('mouseleave', 'li', function() {
			$(this).removeClass('hover').children('ul').stop(true, true).fadeOut(50);
		});

$('#filters.desktop li ul').mouseenter(function(){
		$(this).parent().find("a").slice(0,1).addClass("active");
	});
	$('#filters.desktop li ul').mouseleave(function(){
		$(this).parent().find("a").slice(0,1).removeClass("active");
	});
	
$('#filters.desktop li ul ul').mouseenter(function(){
		$(this).parent().find("a").slice(0,1).removeClass("active");
	});
} else {
	$("ul#filters.desktop").off('mouseenter', 'li').off('mouseleave', 'li');
	$("ul#filters").addClass('mobile').removeClass('desktop');
	$("ul#filters li").css({ 'display' : 'block' });
}

$(window).resize(function(){

if( $(window).width() > 960 ){
$("ul#filters").addClass('desktop').removeClass('mobile');	
$("ul#filters.desktop").on('mouseenter', 'li', function() {
			var $this    = $(this),
				$subMenu = $this.children('ul');
			if( $subMenu.length ) $this.addClass('hover');
			$subMenu.hide().stop(true, true).slideFadeToggle(200);
		}).on('mouseleave', 'li', function() {
			$(this).removeClass('hover').children('ul').stop(true, true).fadeOut(50);
		});

$('#filters.desktop li ul').mouseenter(function(){
		$(this).parent().find("a").slice(0,1).addClass("active");
	});
	$('#filters.desktop li ul').mouseleave(function(){
		$(this).parent().find("a").slice(0,1).removeClass("active");
	});
	
$('#filters.desktop li ul ul').mouseenter(function(){
		$(this).parent().find("a").slice(0,1).removeClass("active");
	});
} else {
	$("ul#filters.desktop").off('mouseenter', 'li').off('mouseleave', 'li');
	$("ul#filters").addClass('mobile').removeClass('desktop');
	$("ul#filters li").css({ 'display' : 'block' });
}

});
	
});
/*-----------------------------------------------------------------------------------*/
/*	SCROLLUP
/*-----------------------------------------------------------------------------------*/
jQuery(function() {

	jQuery(window).scroll(function() {
		if(jQuery(this).scrollTop() != 0) {
			jQuery('#toTop, #backtotop').fadeIn();	
		} else {
			jQuery('#toTop, #backtotop').fadeOut();
		}
	});
	jQuery('#toTop, #options a').click(function() {
		jQuery('body,html').animate({scrollTop:0},200);
	});	
	
});