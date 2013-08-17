$(document).ready(function ($) {
  
    // Sidebar Toggle
    
    $('.btn-navbar').click( function() {
	    $('html').toggleClass('expanded');
    });
    
    
    // Slide Toggles
    
    $('#section3 .button').on('click', function () {
	    
	    var section = $(this).parent();
		
		section.toggle();
	    section.siblings(".slide").slideToggle('2000', "easeInQuart");
	});
	
	$('#section3 .read-more').on('click', function () {
	    
	    var section = $(this).parent();
		
		section.toggle();
	    section.siblings(".slide").slideToggle('2000', "easeInQuart");
	});
	
	$('#section2 .article-tags li').on('click', function () {
	    
	    var section = $(this).parents('.span4');
	    var category = $(this).attr('data-blog');
	    var articles = section.siblings();
	    
	    // Change Tab BG's
	    $(this).siblings('.current').removeClass('current');
	    $(this).addClass('current');
		
		// Hide/Show other articles
	    section.siblings('.current').removeClass('current').hide();
	    
    	$(articles).each(function (index) {
	    	
	    	var newCategory = $(this).attr('data-blog');
	    	
	    	if ( newCategory == category ) {
		    	$(this).slideDown('1000', "easeInQuart").addClass('current');
	    	}
	    });

	});
	
	
		
	// Waypoints Scrolling
	
	var links = $('.navigation').find('li');
	var button = $('.goto-section button');
    var section = $('section');
    var mywindow = $(window);
    var htmlbody = $('html,body');

    
    section.waypoint(function (direction) {

        var datasection = $(this).attr('data-section');

        if (direction === 'down') {
            $('.navigation li[data-section="' + datasection + '"]').addClass('active').siblings().removeClass('active');
        }
        else {
        	var newsection = parseInt(datasection) - 1;
            $('.navigation li[data-section="' + newsection + '"]').addClass('active').siblings().removeClass('active');
        }

    });
    
    mywindow.scroll(function () {
        if (mywindow.scrollTop() == 0) {
            $('.navigation li[data-section="1"]').addClass('active');
            $('.navigation li[data-section="2"]').removeClass('active');
        }
    });
    
    function goToByScroll(datasection) {
        
        if (datasection == 1) {
	        htmlbody.animate({
	            scrollTop: $('.section[data-section="' + datasection + '"]').offset().top
	        }, 500, 'easeOutQuart');
        }
        else {
	        htmlbody.animate({
	            scrollTop: $('.section[data-section="' + datasection + '"]').offset().top + 70
	        }, 500, 'easeOutQuart');
        }
        
    }

    links.click(function (e) {
        e.preventDefault();
        var datasection = $(this).attr('data-section');
        goToByScroll(datasection);
    });
    
    button.click(function (e) {
        e.preventDefault();
        var datasection = $(this).attr('data-section');
        goToByScroll(datasection);
    });
  
    // Snap to scroll (optional)
    
    /*

    section.waypoint(function (direction) {

        var nextpos = $(this).attr('data-section');
        var prevpos = $(this).prev().attr('data-section');

        if (nextpos != 1) {
	        if (direction === 'down') {
	            htmlbody.animate({
		            scrollTop: $('.section[data-section="' + nextpos + '"]').offset().top
		        }, 750, 'easeOutQuad');
	        }
	        else {
	            htmlbody.animate({
		            scrollTop: $('.section[data-section="' + prevpos + '"]').offset().top
		        }, 750, 'easeOutQuad');
	        }
        }
        

    }, { offset: '60%' });	
    
    */
   
       
    
    
    // Redirect external links
	
	$("a[rel='external']").click(function(){
		this.target = "_blank";
	}); 	
	
	
	// Modernizr SVG backup
	
	if(!Modernizr.svg) {
	    $('img[src*="svg"]').attr('src', function() {
	        return $(this).attr('src').replace('.svg', '.png');
	    });
	}    

	
	$("#site_end").click(function() {
		$("html, body").animate({ scrollTop: 0 }, "slow");
		return false;
	});
	
	jQuery(document).ready(function( $ ) {
		// Triggering only when it is inside viewport
		jQuery('.knob-4').waypoint(function(){         		        		        
			// Triggering now
	        jQuery('.knob-4').knob();     
	        // Animating the value
	        if(jQuery('.knob-4').val() == 0) {	
		    	jQuery({value: 0}).animate({value: jQuery('.knob-4').attr("rel")}, {
		        	duration: 5000,
		        	easing:'swing',
		        	step: function() 
			        	{
				            jQuery('.knob-4').val(Math.ceil(this.value)).trigger('change');
				        }
			    	})
		   	}	        	   	        
   	        }
	        ,{
	          triggerOnce: true,
	          offset: function(){
	            return $(window).height() - $(this).outerHeight(); 
	          }
	        }
        );    
	});
});


function MessageBoard (board_data) {
	// construct
    this.messages = null;
    this.contacts = null;
    this.recipient = null;  // recipient of convo with currently 
    		  	  	 	    // signed in user

	// methods: internal
    this._displayMessage = function(username, thumbnail, message, htmlclass) {
    	username = "<b>" + username + "</b><br \>";
    	thumbnail = "<img src='" + thumbnail + "'>";
    	var htmlMessage = "<div class='alert " + htmlclass + "'>" +
    	                                                thumbnail + 
    	                                                 username + 
    	                                                  message + 
                          "</div>";
    	$("#msg-board").append(htmlMessage);
    };

    this._displayContact = function(contact) {
    	$("#contacts").append("<option value='" + contact.id + "'>"
    			                       + contact.name +
    			              "</option>");
    }

 // methods: external
    this.update = function(convo, contacts) {
	    this.conversation = convo;
	    this.contacts = contacts;

    	/* Handle convo length of 0 */
    	$("#msg-board").empty();
    	$("#contacts").empty();

    	for (var i = 0; i < this.contacts.length; i++) {
    		var contact = this.contacts[i];
    		this._displayContact(contact);
    	}

    	var convoLength = this.conversation.length;

    	if (convoLength < 1) {
    		console.log("-- No convo! --");
    		return null;
    	}
	
    	// randomly select the first user in the convo as the person who will
    	// appear on the left side of the message board
    	var preDefinedSender = this.conversation[0].sender.gapi_id;

    	for (var i = 0; i < convoLength; i++) {
    		var msg = this.conversation[i];
    		var sender = msg.sender;
    		if (sender.gapi_id == preDefinedSender) {
                // left
                this._displayMessage(sender.name,
                		             sender.thumbnail,
                		             msg.msg,
                		             "left");
            } else {
                // right
                this._displayMessage(sender.name,
                		             sender.thumbnail,
                		             msg.msg,
                		             "right");
            }
    	}
    };
}

var msgBoard = new MessageBoard();

function updateMessageBoard(recipient) {
	if (recipient == undefined)
		recipient = null;
    $.ajax({
        type : 'GET',
        url : '/messageboard/' + recipient,
        success : function(board_data) {
            msgBoard.update(board_data.convo, board_data.contacts);
        },
    });
}