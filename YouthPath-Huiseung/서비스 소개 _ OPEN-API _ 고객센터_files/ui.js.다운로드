/* 《 고용24 공통 UI js 》 */
var ui = {};


var keyInput ={
	/* 숫자만 */
	numberOnly: function(el) {
		el.value = el.value.replace(/[^0-9]/g, '');
	}
}

/* 1204 수정 */
ui.focusRotation = function(tgEl) {
	var $tgEl = tgEl;
	var tgEl = '[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])';
	var focusTg = $tgEl.find(tgEl);
	var $firstFocusEl = focusTg.first();
	var $lastFocusEl = focusTg.last();

	$lastFocusEl.on({
		'keydown': function(e) {
			var _keyCode = e.keyCode || e.which;
			if(_keyCode === 9) {
				if(!e.shiftKey) {
					e.preventDefault();
					$firstFocusEl.focus();
				}
			}
		}
	});
}

//tab
ui.tab = function(){
	$('.tab_title li').on('click', function () {
		var onTab = $(this).attr('aria-controls');

		$(this).parent('.tab_title').children('li').removeClass('active').children('button').attr('aria-selected', false);
		$(this).parent('.tab_title').siblings('.tab_cont').children('.box_tab-contents').removeClass('active').attr({
			'hidden': true
			//, 'tabindex': -1
		});
		$(this).addClass('active').children('button').attr('aria-selected', true);
		$('#' + onTab).addClass('active').attr({
			'hidden': false
			//, 'tabindex': 0
		});
	});
}


// Dim
ui.dimShow = function(){ /* 딤드 show */
	$("body").addClass("dim");
}
ui.dimHide = function(){ /* 딤드 hide */
	$("body").removeClass("dim");
}
ui.fullPopup = function(){ //팝업

	var $openBtn = $(".full_open"),
		$closeBtn = $(".full_pop .closed");

	$('.full_pop').each(function() {
		$(this).attr('tabindex', '0');
	});

	var $btn = null;

	console.log("ui.fullPopup=======================");

	$openBtn.on("click", function(e) { /* 열기 */
		e.preventDefault();
		$btn = $(this);
		var target = $(this).attr("open-full-pop") || e;
		var layer = $(".full_pop" + "." + target);

		console.log("openBtn click ========================", layer);

		if(layer.find('.tab_title').length) {
			layer.addClass('tab_style');
		}
		layer.fadeIn(150).addClass("on");
		layer.focus();
		ui.dimShow();

		var x = layer.find('> .closed');
		x.on('keydown', function() {
			if (window.event.keyCode === 9) {
				layer.focus();
			}
		});

		let timer = setTimeout(function() {
		// 기본 스크립트 실행
		$(".toast_pop").length && ui.toastPop(); //토스트팝업
		$('.btn_form').length && ui.fullText(); // 전문보기
		$(".box_tooltip").length && ui.tooltip(); // 툴팁
		$(".acd").length && ui.accordion(); // 아코디온
		$("table").length && ui.tableCaption(); // 테이블 캡션 넣기
			$(".box_tooltip").length && ui.tooltip();
		}, 200)
	});

	$closeBtn.on("click", function() { /* 닫기 */
		var target= $(this).closest(".full_pop");
		target.fadeOut(150).removeClass("on");
		ui.dimHide();
		$btn = $btn ?? $(this);
		$btn.focus();
	});
}

ui.fullLayerPopup = function(callObjId){ //팝업
	var $openBtn = $(".full_open"),
		$closeBtn = $(".full_pop .closed");

	$('.full_pop').each(function() {
		$(this).attr('tabindex', '0');
	});

	var $btn = callObjId;

	ui.tableCaption();

	$closeBtn.off('click').on("click", function() { /* 닫기 */

		var target= $(this).closest(".full_pop");
		$btn = $btn ?? $(this);
		target.fadeOut(150, function(){
			$btn.focus();
		}).removeClass("on");

		//if($(target).prop("id") != 'agreePopUp'){
			ui.dimHide();
		//}
	});


	//원래
	//$closeBtn.off('click').on("click", function() { /* 닫기 */
	//	var target= $(this).closest(".full_pop");
	//	$btn = $btn ?? $(this);
	//	target.fadeOut(150, function(){
	//		$btn.focus();
	//	}).removeClass("on");
	//	ui.dimHide();
	//});
}

ui.fullLayerSiteMapPopup = function(callObjId){ //팝업
	var $openBtn = $(".full_pop_site"),
		$closeBtn = $(".full_pop_site .siteMap_ico09");

	$('.full_pop_site').each(function() {
		$(this).attr('tabindex', '0');
	});

	var $btn = callObjId;

	ui.tableCaption();

	$closeBtn.off('click').on("click", function() { /* 닫기 */

		$(document).off("keydown");

		var target= $(this).closest(".full_pop_site");
		target.fadeOut(150).removeClass("on");
		ui.dimHide();
		$btn = $btn ?? $(this);
		$btn.focus();

	});
}

// ui.childPopup = function(pForm){ //팝업
// 	var $openBtn = $("#childLayer_dialog .full_open"),
// 		$closeBtn = $("#childLayer_dialog .full_pop .closed");

// 	$closeBtn.on("click", function() { /* 닫기 */
// 		var target= $(this).closest("#childLayer_dialog .full_pop");
// 		target.fadeOut(150).removeClass("on");
// 		//ui.dimHide();
// 		$("#"+pForm).removeClass("layer_dim");
// 	});
// }

// ui.alertPopup = function(){ //알럿
// 	var $openBtn = $(".btn_alert"),
// 		$closeBtn = $(".alert_pop .closed");

// 	$openBtn.on("click", function(e) { /* 열기 */
// 		e.preventDefault();
// 		var target = $(this).attr("open-layer-class") || e;
// 		$(".alert_pop" + "." + target).fadeIn(150).addClass("on");
// 		ui.dimShow();
// 	});

// 	$closeBtn.on("click", function() { /* 닫기 */
// 		var target= $(this).closest(".alert_pop");
// 		var popOn = $(".alert_pop.on").length;

// 		target.fadeOut(150).removeClass("on");
// 		if(popOn <= 1){ // 팝업 2개 이상 활성화될 경우 dim 닫지 않기
// 			ui.dimHide();
// 		}
// 	});
// };

ui.toastPop = function (){ //토스트팝업
	var $toastBtn = $(".btn_toast"),
		$toast = $(".toast_pop");
		$tostCloseBtn = $(".toast_pop .closed");

	$toastBtn.on("click", function(e){
		e.preventDefault();
		var target = $(this).attr("open-toast-pop") || e;
		$(".toast_pop" + "." + target + "").addClass("active");

		setTimeout(function(){
			$toast.removeClass("active")
		}, 3000);
	});

	$tostCloseBtn.on("click", function() { /* 닫기 */
		$toast.removeClass("active")
	});
}

// 모바일
// ui.bottomSheet = function(){ //바텀시트팝업
// 	var $openBtn = $(".sheet_open"),
// 		$closeBtn = $(".bottom_sheet .closed");

// 	$(".bottom_sheet").css("display", "none");
// 	$openBtn.on("click", function(e) { /* 열기 */
// 		e.preventDefault();
// 		var target = $(this).attr("open-bottom-sheet") || e;
// 		$(".bottom_sheet" + "." + target).slideDown().addClass("on");
// 		ui.dimShow();
// 	});

// 	$closeBtn.on("click", function() { /* 닫기 */
// 		var target= $(this).closest(".bottom_sheet");
// 		target.slideUp().removeClass("on")
// 		ui.dimHide();
// 	});
// }

//전문닫기 토글
ui.fullText = function() {
	$('.btn_form').click(function(){
    var btnForm = $(this).hasClass('active');
    var parentDiv = $(this).parents('div'); // .btn_form의 부모 div 요소를 찾습니다.

    if (!parentDiv.hasClass('cont_tit')) {
        // 만약 .btn_form의 부모 요소에 .cont_tit 클래스가 없다면
        if (btnForm) {
            $(this).removeClass('active');
            $(this).next().removeClass('active');
            $(this).attr('aria-expanded', 'false');
            $(this).text('전문보기');
        } else {
            $(this).addClass('active');
            $(this).next().addClass('active');
            $(this).attr('aria-expanded', 'true');
            $(this).text('전문닫기');
        }
    } else {
        // 만약 .btn_form의 부모 요소에 .cont_tit 클래스가 있다면
        if (btnForm) {
            $(this).removeClass('active');
            $(parentDiv).next().removeClass('active');
            $(this).attr('aria-expanded', 'false');
            $(this).text('자세히보기');
        } else {
            $(this).addClass('active');
            $(parentDiv).next().addClass('active');
            $(this).attr('aria-expanded', 'true');
            $(this).text('자세히보기');
        }
    }
});
}

ui.btnLayer = function() {
	$('.btn_open').off('click').on('click', function(){
		var btnToggle = $(this).hasClass('active');
		if(btnToggle){
			$(this).removeClass('active');
			$(this).next().hide();
			$(this).attr({'aria-expanded':'false','title':'열기'});
		}else{
			$(this).addClass('active');
			$(this).next().show();
			$(this).attr({'aria-expanded':'true','title':'닫기'});
		}
	});
		$('.ui_layer .btn_close').off('click').on('click', function(){
		$(this).closest('.ui_layer').hide().prev('.btn_open').removeClass('active');
	});
}

//툴팁
ui.tooltip = function() {
	var $lastBtn = null;
	$(".box_tooltip [class*='btn']").attr('aria-expanded', 'false');
	$(".box_tooltip [class*='btn']").click(function(){
		$lastBtn = $(this);
		var tooltip = $(this).next('.box_help-data').hasClass('active');
		if(tooltip){
			$(this).attr('aria-expanded', 'false').next('.box_help-data').removeClass('active');
		}else{
			$('.btn_help').next('.box_help-data').removeClass('active');
			$(this).attr('aria-expanded', 'true').next('.box_help-data').addClass('active');
		}
	});
	$('.tooltip_close').click(function(){
		$(this).parent('.box_help-data').removeClass('active').siblings("[class*='btn']").attr('aria-expanded', 'false');
		$lastBtn.focus();
	});
}

// onclick용 tooltip
function tooltipBtn(item) {
	item.classList.toggle('active');
}
function tooltipClose(item){
	item.parentElement.previousElementSibling.classList.remove('active');
}

//아코디언
ui.accordion = function() {
	$('.acd_btn').click(function(){
		if($(this).hasClass('acd_open')){
			$(this).removeClass('acd_open');
			$('.acd.slide_type ul > li, .acd_slide').removeClass('on').attr('aria-expanded', 'true');
			$('.acd.slide_type ul > li .acd_cont, .acd_slide .acd_cont').stop().slideUp();
			$(this).find('.txt').text("펼치기");
		} else {
			$(this).addClass('acd_open');
			$('.acd.slide_type ul > li, .acd_slide').addClass('on').attr('aria-expanded', 'false');
			$('.acd.slide_type ul > li .acd_cont, .acd_slide .acd_cont').stop().slideDown();
			$(this).find('.txt').text("접기");
		}
	});
	$('.acd:not(.type03) > ul > li > *:first-child').attr('role', 'button');
	$('.acd:not(.type03) > ul > li > *:first-child').off('click').on('click', function() {
		if($(this).parent().hasClass('on')) {
			$(this).parent().find('.acd_cont').stop().slideUp();
			$(this).attr('aria-expanded', 'false');
			$(this).parent().removeClass('on');
		} else{
			$(this).parent().closest('.acd').find('> ul > li').removeClass('on');
			$(this).parent().closest('.acd').find('> ul > li .acd_cont').stop().slideUp();
			$(this).parent().find('.acd_cont').stop().slideDown();
			$(this).attr('aria-expanded', 'true');
			$(this).parent().addClass('on');
		}
	});
}

// .acd > ul > li > .b1_sb, .acd > ul > li > *:first-child

// 추가 검색조건 열기/닫기
ui.slideMore = function() {
	$('.btn_slide_more').click(function(){
		$(this).attr('role', 'button');
		var _text = $(this).find('.txt');
		var slideBtn = $(this).hasClass('on');
		if(slideBtn){
			$(this).removeClass('on');
			$('.slide_cont').stop(true,true).slideDown();
            $(this).attr('aria-expanded', 'true');
			_text.text('닫기');
		}else{
			$('.slide_cont').stop().slideUp();
			$(this).addClass('on');
            $(this).attr('aria-expanded', 'false');
			_text.text('열기');
		}
	});
}

// table caption 넣기
ui.tableCaption = function() {
	$('table:not(.notCaption)').each(function() {
		var ths = $(this).find('th');

		if(ths.length) {

			var arr = new Array();
			$(this).find('caption').remove();
			ths.each(function(idx, th) {
				if($(th)[0].firstChild)
					arr.push($(th)[0].firstChild.data || $(th).text());
				});
			if(arr.length > 0) {
				var captionContents = arr.join();
				var caption = `${captionContents}을(를) 제공하는 표`;
				$(this).prepend(`<caption>${caption}</caption>`);
			} else {
				$(this).prepend(`<caption>고용24에서 제공하는 표</caption>`);
			}
		}
	});
}
// breadcrumb
ui.breadcrumb = function() {
	var subBtn = $('.location > ul > li.sub > button');
	subBtn.on('click', function() {
		if ($(this).hasClass('on')) {
			$(this).removeClass('on');
			$(this).closest('li').find('.breadcrumb-layer').hide();
		} else {
			subBtn.removeClass('on');
			$(this).addClass('on');
			$('.breadcrumb-layer').hide();
			$(this).closest('li').find('.breadcrumb-layer').show();
		}
	});
}

ui.scrollEvent = function() {
	$('.cont_wrap_area').each(function() {
		const $this = $(this);
		var box = $this.find('.scroll');
		var tabList = $this.find('.tab_title > li');
		var btn = $this.find('.tab_title > li > button');

		tabList.removeClass('active');
		btn.attr('aria-selected', false);
		tabList.eq(0).addClass('active');
		btn.eq(0).attr('aria-selected', true);

		$(window).scroll(function() {
			var scroll = $(this).scrollTop();
			if (scroll > 192) {
				$this.find(".tab_title_wrap").addClass("fixed");
			}
			else {
				$this.find(".tab_title_wrap").removeClass("fixed");
			}
			box.each(function(index, item) {
				if (item.getBoundingClientRect().top < 260) {

					tabList.removeClass('active');
					btn.attr('aria-selected', false);
					tabList.eq(index).addClass('active');
					btn.eq(index).attr('aria-selected', true);

					if (tabList.eq(2).hasClass('active')){
						$('.floating_bottom_area').addClass("show");
					}
					else {
						$(".floating_bottom_area").removeClass("show");
					}
				}
			});
		});
		btn.off('click').on('click', function() {
			var myIndex = $(this).parent('li').index();
			$('html, body').stop().animate({ scrollTop : (box.eq(myIndex).offset().top) - 259 }, 200);
		});
	});
}

/* 251226 설문조사 신설 UI | 김무현 START */
/*
	고객센터
*****************************************************/

/* 공지사항 - 설문조사 */
ui.imagePop = {
	clickButton: null,
	init:function() {
		$('.JS-imgpop').on('click', ui.imagePop.click);
		$('.image_pop .ptn_close').on('click', ui.imagePop.close);
	},
	click:function() {
		ui.imagePop.clickButton = $(this);
		var src = $(this).find('img').attr('src');
		var alt = $(this).find('img').attr('alt');

		$('body').addClass('dim');
		$('.image_pop').show().find('.img_view img').attr('tabindex', '0').focus();
		$('.image_pop .img_view img').attr({'src': src, 'alt': alt});

		ui.focusRotation($('#image_popid'));
	},
	close:function() {
		$('body').removeClass('dim');
		$('.image_pop').hide();
		$('.image_pop .img_view img').attr({'src': '', 'alt': ''});
		ui.imagePop.clickButton.focus();
		ui.imagePop.clickButton = null;
	}
}

/* 251226 설문조사 신설 UI | 김무현 END */

/*
	마이페이지
*****************************************************/

/* 홈 신규 리뉴얼 - 서비스 현황 */
ui.mypageHome = {
	_alramClickCallbacks: [],
	getZoom:() => parseFloat($('body').css('zoom') || 1),
	getCardList: () => $('.JS-myMaintabs').siblings('.target').find('.card .dropdown'),
	getTargetTab: ($tab) => {
		$('.JS-myMaintabs').siblings('.target').find('.subject').attr('aria-expanded', false);
		var controlId = $tab.attr('aria-controls');
		return $('.JS-myMaintabs').siblings('.target').find('#'+controlId);
	},
	init:function() {
		$('.JS-myMaintabs .main_tab').on('click', ui.mypageHome.click).first().attr('title', '선택됨');
		$('.JS-myAlram').on('click', ui.mypageHome.alramClick);
		$('.mypage .home .condition .subject').on('click', ui.mypageHome.dropdown);

		ui.mypageHome.myHover(); /* 주소 호버 시 */

		// 스크롤 이벤트
		// var resizeTimeout;
		// $(window).on('scroll', function() {
		// 	clearTimeout(resizeTimeout);
		// 	resizeTimeout = setTimeout(function() {
		// 		ui.mypageHome.scrollEvent();
		// 	}, 10);
		// });
	},
	/* 스크롤 */
	scrollEvent:function() {
		var $JSmyMaintabs = $('.JS-myMaintabs');
		var $buttons = $JSmyMaintabs.find('.main_tab');
		var $card = $JSmyMaintabs.siblings('.target').find('.card');

		var scrollPos = window.scrollY;
		var zoom = parseFloat($('body').css('zoom') || 1);

		$card.each(function(index, elm) {
			var _rectTop = this.offsetTop;
			var _offsetTop = Math.floor(_rectTop * zoom);

			if(scrollPos >= _offsetTop - (275 * zoom)) {
				$buttons.removeClass('active').attr('aria-expanded', false)
				.eq(index).addClass('active').attr('aria-expanded', true);
			}
		});
		// 메인탭 그림자 추가
		if(scrollPos >=  Math.floor($JSmyMaintabs.siblings('.target')[0].offsetTop - (270 / zoom))) {
			$JSmyMaintabs.addClass('shadow');
		} else {
			$JSmyMaintabs.removeClass('shadow');
		}
	},
	/* 메인탭 클릭 시 */
	click:function(event) {
		var $this = $(event.currentTarget);
		var $target = ui.mypageHome.getTargetTab($this);
		var zoom = ui.mypageHome.getZoom();

		if($target.is(':hidden')) {
			ui.mypageHome.listShow(event); /* 목록 뿌려줌 */

			/* 해당 타겟으로 포커스 이동 */
			setTimeout(function() {
				$target.siblings('.subject').attr('aria-expanded', true).focus();
			},220)

		} else {
			var _offsetTop = Math.floor($target[0].closest('.card').offsetTop * zoom);

			$target.siblings('.subject').attr('aria-expanded', true).focus();
			$('html, body').stop().animate({scrollTop: _offsetTop - (268 * zoom)},400);
		}

		// ui.mypageHome.expandAll(); /* 모두 펼치기/접기 체크 */
	},
	/* 카드 안에 있는 토글 버튼 클릭 시 */
	dropdown:function(event, all) {
		var $wrapper = $('.JS-myMaintabs').siblings('.target');
		var $cards = $wrapper.find('.card .dropdown');
		var $buttons = $wrapper.find('.subject');
		var $expand = $('.mypage .home .title_wrap .expand');

		if(all) {
			var expanded = $expand.attr('aria-expanded') === 'true';
			$expand.attr('aria-expanded', !expanded).find('span').text(expanded ? '모두 펼치기' : '모두 접기');
			$cards.each(function() {
				expanded ? $(this).slideUp(200) : $(this).slideDown(200);
			})
			$buttons.attr('aria-expanded', !expanded);
			return;
		}

		var $trigger = $(event.currentTarget);
		var $dropdown = $trigger.closest('.card').find('.dropdown');
		var isHidden = $dropdown.is(':hidden');
		if(isHidden) {
			ui.mypageHome.listShow(event); /* 목록 뿌려줌 */
		} else {
			$trigger.attr('aria-expanded', false);
			$dropdown.slideUp(200);
		}
		// ui.mypageHome.expandAll(); /* 모두 펼치기/접기 체크 */
	},
	/* 모두 펼치기/접기 체크 */
	expandAll:function() {
		var $expand = $('.mypage .home .title_wrap .expand')

		var allOpen = $('.mypage .home .card').find('.subject').filter(function() {
			return $(this).attr('aria-expanded') === 'true';
		}).length === $('.mypage .home .card').find('.subject').length;
		if(allOpen === true) {
			$expand.attr('aria-expanded', true).find('span').text('모두 접기');
		} else {
			$expand.attr('aria-expanded', false).find('span').text('모두 펼치기');
		}
	},
	/* 목록 뿌려줌 */
	listShow:function(event) {
		var $this = $(event.currentTarget);
		var $target = ui.mypageHome.getTargetTab($this);
		var $card = ui.mypageHome.getCardList();
		var zoom = ui.mypageHome.getZoom();

		// 인덱스 조정 및 속성 추가
		var targetIndex;
		if($this.attr('class') === 'subject') {
			targetIndex = $this.parents().index();
		} else {
			targetIndex = $this.index();
		}
		$('.service_wrap .card .subject').eq(targetIndex).attr('aria-expanded', true);
		$('.maintabs .main_tab').removeClass('active').attr('aria-expanded', false).removeAttr('title').eq(targetIndex).addClass('active').attr({'aria-expanded': true, 'title': '선택됨'}); /* 11-27 추가 */
		$card.find('.subject').attr('aria-expanded', false);
		$this.attr('aria-expanded', true)
		$card.hide();

		// 스크롤 위치 조정
		var _offsetTop = Math.floor($target[0].closest('.card').offsetTop * zoom);
		$card.eq($this.index()).find('.subject').attr('aria-expanded', true);
		$('html, body').stop().animate({scrollTop: _offsetTop - (268 * zoom)},400);
		$target.slideDown(200);
	},

	/* 알람 클릭 시 */
	alramClick:function() {
		var $mypageHome = $('.mypage .home');
		var $notice = $mypageHome.find('.notice');
		var $cardEffect = $mypageHome.find('.card_effect');
		var $alram = $mypageHome.find('.alram');

		$cardEffect.addClass('active');
		addDelay($cardEffect.find('.front'));
		$notice.removeClass('hide').find('h4').focus();

		/* 알람 탭 클릭 */
		$alram.find('.alram_tab').on('click', function() {
			var _labelledby = $(this).attr('id');
			$alram.find('.alram_tab').removeClass('active');
			$(this).addClass('active').siblings().attr('aria-selected', 'false');
			$(this).attr('aria-selected', 'true').closest('.alramtabs').siblings('.sub_target').attr('aria-labelledby', _labelledby);
		});

		/* 내용 클릭 */
		$notice.find('.item_alram a').on('click', function() {
			$notice.find('.item_alram a').removeClass('act').attr('aria-expanded', 'false');
			$(this).addClass('act').attr('aria-expanded', 'true');
		});

		/* 닫기 */
		$notice.find('.close').on('click', function() {
			addDelay($notice);
			$mypageHome.find('.front').removeClass('hide');
			$notice.find('.item_alram a').attr('aria-expanded', 'false').removeClass('act');
			$cardEffect.removeClass('active').find('.front').find('.bell').focus();
		});

		function addDelay(selector, delay = 300) {
			setTimeout(function() {
				selector.addClass('hide');
			},delay);
		}
	},
	/* 주소 호버 시 */
	myHover:function() {
		var speedPerPx = 15;
		function setTransform($el, x, duration) {
			$el.css({
				transition: duration ? `transform ${duration}ms linear` : 'none',
				transform: `translateX(${x}px)`
			})
		}
		$('.JS-myHover').hover(function() {
			var $text = $(this).find('.strong');
			var wrapperWidth = $(this).width();
			var textWidth = $text[0].scrollWidth;
			if( textWidth <= wrapperWidth) return;

			var distance = textWidth + 50;
			var duration = Math.max(distance * speedPerPx, 300);
			var currentX = 0;
			var matrix = $text.css('transform');
			if(matrix && matrix !== 'none') {
				var values = matrix.match(/matrix\((.+)\)/)
				if(values) currentX = parseFloat(values[1].split(', ')[4]);
			}
			var firstDuration = duration * 0.7;
			setTransform($text, currentX, 0);
			void $text[0].offsetWidth;
			setTransform($text, -distance, firstDuration);

			var loopSlide = () => {
				setTransform($text, wrapperWidth, 0);
				void $text[0].offsetWidth;
				setTransform($text, -distance, duration);
				$text.one('transitionend', () => {
					if($text.data('hovering')) loopSlide();
				})
			}
			$text.data('hovering', true);
			$text.off('transitionend').one('transitionend', loopSlide);
		}, function() {
			var $text = $(this).find('.strong');
			$text.data('hovering', false);
			$text.off('transitionend');
			setTransform($text, 0, 300);
		}
	)}
}



// 퍼블용 include
$(function(){
	var includes = $('[data-include]');
	jQuery.each(includes, function(){
		var file = '/cm/pub/include/' + $(this).data('include') + '.html';
		//$(this).load(file);
	});
});

//프린트
$(document).on("click touchstart", ".lct_btn_print", function(e){
	window.print();
});

//input type reset
$(document).on("click","button[type=reset]",function(e){


	$('table').length && ui.tableCaption(); // 테이블 캡션넣기
	e.preventDefault();
	$(this).prev().val("");
});

$(function(){
	// $(".alert_pop").length && ui.alertPopup(); //알럿
	$(".full_pop").length && ui.fullPopup(); //팝업
	$(".toast_pop").length && ui.toastPop(); //토스트팝업
	$('.btn_form').length && ui.fullText(); // 전문보기
	$(".box_tooltip").length && ui.tooltip(); // 툴팁
	$(".acd").length && ui.accordion(); // 아코디온
	$('.btn_slide_more').length && ui.slideMore(); // 추가 검색조건 열기/닫기
	$('table').length && ui.tableCaption(); // 테이블 캡션넣기
	$('.location').length && ui.breadcrumb(); // breadcrumb 레이어
	$('.btn_open').length && ui.btnLayer(); //  토글버튼
	$('.mypage .home').length && ui.mypageHome.init(); //  마이페이지 홈 신규 리뉴얼
	$('.image_pop').length && ui.imagePop.init(); //  설문조사 이미지 팝업 - 251226 설문조사 신설 UI | 김무현 START


	//즐겨찾기 토글
	/*
	$('.lct_btn_fav').click(function(){
		$(this).toggleClass('active');
	});
	*/

	//좋아요 토글
	$('.ico24_ui_like').click(function(){
		$(this).toggleClass('active');
	});

	/* 250618 메인메뉴(GNB) HTML 수정 임정규 */
	// gnb
	var preventFocus = false;
	var $gnb = $('#gnb');
	var $JSsearchToggle = $(".JS-searchToggle");
	var isGnbOpen = false;

	// GNB 1depth: 클릭 및 포커스 이벤트
	$gnb.find('>ul >li >a')
		.on('mousedown', function () {
			preventFocus = true;
		})
		.on('click', function (e) {
			e.preventDefault();
			handleGNBDepth1($(this));
		})
		.on('focusin', function () {
			if (preventFocus) {
				preventFocus = false;
				return;
			}
			handleGNBDepth1($(this));
		});

	// GNB 2depth: 클릭 및 포커스 이벤트
	$gnb.find('.gnb2depth >li >a').on({
		'click focusin': function (e) {
			if ($(this).attr('title') === '새창 열림') return;

			e.preventDefault();

			if ($(this).attr('title') === '선택됨') return;

			$gnb.find('.gnb2depth > li > a').not(this).not(".btn_link_new").attr('title', '');
			$gnb.find('.gnb3depth').removeClass('active');

			setTimeout(function () {
				$(this).attr('title', '선택됨').siblings('.gnb3depth').addClass('active');

				var $gnb2 = $(this).closest('.gnb2depth');
				var _gnb2height = Math.floor($gnb2.height());
				var _gnb3height = Math.floor($(this).siblings('.gnb3depth').height());
				var maxHeight = Math.max(_gnb2height, _gnb3height);

				$('.new #header_bottom').height(maxHeight + 112);
			}.bind(this), 100);
		}
	});

	// GNB 1depth 처리 함수
	function handleGNBDepth1($this) {
        // aria-hidden 처리
        var ariaTarget = $("#wrap").children("section, footer");


		/* 화면확대축소 닫기 */
		$('.JS-screenToggle').attr('aria-expanded', false).siblings('div').removeClass('active');

		/* 검색 닫기 - 검색리뉴얼 */
		 $JSsearchToggle.removeClass('on').attr('aria-pressed', false);;
		/* $('#header_menutree .sub_search_wrap').removeClass('active');*/

		/* dimmed 클릭 시 닫기 */
		$('.dimmed').off().on('click', function() {
			if(!isGnbOpen) return;

			//GNB 닫기
			isGnbOpen = false;
			$(this).removeClass('active');

			$('#header_bottom').removeClass('extend').height(0);
			$gnb.find('>ul >li >a').attr('aria-expanded', false);
			$gnb.find('.gnb2depth').removeClass('active'); //.find('>li >a').not(".btn_link_new").attr('title', '');
			$gnb.find('.gnb3depth').removeClass('active');

			// 검색 닫기 - 검색리뉴얼
			$JSsearchToggle.removeClass('on').attr('aria-pressed', false);
			ariaTarget.removeAttr("aria-hidden");
			/* $('#header_menutree .sub_search_wrap').removeClass('active');*/

		})

		if ($this.attr('aria-expanded') === 'true') {
			// 닫기
			isGnbOpen = false;
			$('.dimmed').removeClass("active");
			$this.closest('#header_bottom').removeClass('extend').height(0);

			$gnb.find('>ul >li >a').attr('aria-expanded', false);
			$gnb.find('.gnb2depth').removeClass('active'); //.find('>li >a').not(".btn_link_new").attr('title', '');
			$gnb.find('.gnb3depth').removeClass('active');
			ariaTarget.removeAttr("aria-hidden");
		} else {
			// 열기
			isGnbOpen = true;
			$('.dimmed').addClass("active");
			$this.closest('#header_bottom').addClass('extend');

			$gnb.find('>ul >li >a').not($this).attr('aria-expanded', false);
			$gnb.find('.gnb2depth').removeClass('active'); //.find('>li >a').not(".btn_link_new").attr('title', '');
			$gnb.find('.gnb3depth').removeClass('active');

			ariaTarget.attr("aria-hidden", true);

			/*
			   현재 열린 화면이 화면 트리에 존재한다면 해당 화면을 active 해준다.
			*/
			var secondDepth = $this.attr('aria-expanded', true).siblings('.gnb2depth').addClass('active');
            if(secondDepth.children("li").children("a[title=선택됨]").length == 1){
                secondDepth.children("li").children("a[title=선택됨]").siblings('.gnb3depth').addClass('active');
            }else{
                secondDepth.children("li").children(':first-child >a').attr('title', '선택됨').siblings('.gnb3depth').addClass('active');
            }


			setTimeout(function () {
				var $gnb2 = $this.siblings('.gnb2depth');
				var _gnb2height = Math.floor($gnb2.height());
				var _gnb3height = Math.floor($gnb2.find('.gnb3depth').height());
				var maxHeight = Math.max(_gnb2height, _gnb3height);

				$('.new #header_bottom').height(maxHeight + 112);
				//$gnb.find('.gnb3depth >li >a').attr('title', '');
			}, 10);
		}

		// 마지막 포커스 요소 처리 (포커스 트랩)
		var $tgEl = $gnb.find('>ul >li').last();
		var focusable = '[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])';
		var focusTg = $tgEl.find(focusable);
		var $lastFocusEl = focusTg.last();

		$lastFocusEl.off('keydown').on('keydown', function (e) {
			var keyCode = e.keyCode || e.which;
			if (keyCode === 9 && !e.shiftKey) {
				e.preventDefault();
				$('.dimmed').removeClass("active");
				$('#header_bottom').removeClass('extend').height(0);
				$gnb.find('>ul >li >a').attr('aria-expanded', false);
				$gnb.find('.gnb2depth').removeClass('active').find('>li >a').not(".btn_link_new").attr('title', '');
				$gnb.find('.gnb3depth').removeClass('active');
				$('.header_allmenu').focus();
			}
		});
	}

	/* 검색 버튼 클릭 - 검색리뉴얼 */
	$JSsearchToggle.on('click', function(e){
		e.preventDefault();
		$layerTs = $('.layer_ts');

		var layerId = $layerTs.attr('id');
		if(!$JSsearchToggle.hasClass('on')) {
			/* GNB 닫기 */
			$('#header_bottom').removeClass('extend').height(0);
			$gnb.find('>ul >li >a').attr('aria-expanded', false);
			$gnb.find('.gnb2depth').removeClass('active').find('>li >a').not(".btn_link_new").attr('title', '');
			$gnb.find('.gnb3depth').removeClass('active');

			$JSsearchToggle.addClass('on').attr('aria-pressed', true);
			$layerTs.show();
			$('#sub_topQuery').focus();

			// 바디 스크롤 제거
			$('body').css('overflow', 'hidden');
			// 퀵메뉴 숨김
			$('.quick_top').css('display', 'none');

			// 포커스 순환
			focusRotation($('#'+layerId));
		}
	});

	$('.layer_ts').find('.layer_ts_closed').on('click', function(){
		var target= $(this).closest(".full_pop");
		target.fadeOut(150).removeClass("on");

		// 바디 스크롤 추가
		$('body').css('overflow', '');
		// 퀵메뉴 보임
		$('.quick_top').css('display', '');

		$JSsearchToggle.removeClass('on').attr('aria-pressed', 'false').focus();
	});

	// 포커스 순환 함수
	var focusRotation = function(tgEl) {
		var $tgEl = tgEl;
		var tgEl = '[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])';
		var focusTg = $tgEl.find(tgEl);
		var $firstFocusEl = focusTg.first();
		var $lastFocusEl = focusTg.last();

		$lastFocusEl.on({
			'keydown': function(e) {
				var _keyCode = e.keyCode || e.which;
				if(_keyCode === 9) {
					if(!e.shiftKey) {
						e.preventDefault();
						$firstFocusEl.focus();
					}
				}
			}
		});
	}
	/* 250618 메인메뉴(GNB) HTML 수정 임정규 */


	/* 20250625 GNB 화면/확대축소 설정(임정규) */
	/* GNB 화면/확대 축소  */
	var $JSscreenToggle = $(".JS-screenToggle");
	var $screenSizeBox = $JSscreenToggle.siblings("div");
	var $zoomButtons = $screenSizeBox.find(".screen button, .screen_btns button.screen_reset");

	// 토글 버튼 클릭 시 screen_size 영역 열고 닫기
	$JSscreenToggle.on('click', function () {
		/* GNB 닫기 */
		$('#header_bottom').removeClass('extend').height(0);
		$gnb.find('>ul >li >a').attr('aria-expanded', false);
		$gnb.find('.gnb2depth').removeClass('active').find('>li >a').not(".btn_link_new").attr('title', '');
		$gnb.find('.gnb3depth').removeClass('active');

		/* 검색 닫기 - 검색리뉴얼 */
		 $JSsearchToggle.removeClass('on').attr('aria-pressed', false);
		 /*$('#header_menutree .sub_search_wrap').removeClass('active');*/

		/* 딤드 닫고 소스 시작 */
		$('.dimmed').removeClass('active');
		var $this = $(this);
		var isExpanded = $this.attr('aria-expanded') === 'true';
		var $targetBox = $this.siblings('div');

		/* 모든 토글 초기화 */
		$JSscreenToggle.attr('aria-expanded', 'false').removeClass('active');
		$JSscreenToggle.siblings("div").removeClass('active');


		// 자기 자신이 열려 있지 않으면 열기
		if(!isExpanded) {
			$this.attr('aria-expanded', 'true').addClass('active');
			$targetBox.addClass('active');
			$('.screen_size .screen .screen_title').attr('tabindex', '-1').focus(); /* 251210 글자·화면 설정 다크모드 선택 추가 */
		}
	});

	// 줌 버튼 클릭 시 동작
	$zoomButtons.on("click", function () {
		var zomm = 1;

		if ($(this).hasClass("btn_size")) {
			$zoomButtons.filter(".btn_size").attr('title', '').removeClass('active');
			$(this).attr('title', '선택됨').addClass('active');
		}

		if ($(this).hasClass("sm")) zomm = 0.9;
		else if ($(this).hasClass("md")) zomm = 1;
		else if ($(this).hasClass("lg")) zomm = 1.1;
		else if ($(this).hasClass("xlg")) zomm = 1.2;
		else if ($(this).hasClass("xxlg")) zomm = 1.3;
		else if ($(this).hasClass("screen_reset")) {
			zomm = 1;
			$zoomButtons.filter(".btn_size").attr('title', '').removeClass('active');
			$screenSizeBox.find("li:eq(1) .btn_size").attr('title', '선택됨').addClass('active');
		}

		localStorage.setItem("gfnDefaultScale", zomm);
		$("body").css("zoom", zomm);
	});

	// 페이지 로딩 시 저장된 줌 값 적용 및 버튼 상태 반영
	var gfnDefaultScale = localStorage.getItem("gfnDefaultScale") || "1";
	$("body").css("zoom", gfnDefaultScale);

	// 버튼 상태 초기화
	var zoomIndexMap = {
		"0.9": 0,
		"1": 1,
		"1.1": 2,
		"1.2": 3,
		"1.3": 4
	};

	var index = zoomIndexMap[gfnDefaultScale];
	if (index !== undefined) {
		$zoomButtons.filter(".btn_size").attr('title', '').removeClass('active');
		$screenSizeBox.find(`li:eq(${index}) .btn_size`).attr('title', '선택됨').addClass('active');
	}

	/* 251210 글자·화면 설정 다크모드 선택 추가 */
	$('.screen_size .screen_close').on('click', function() {
		$JSscreenToggle.attr('aria-expanded', false).removeClass('active').focus().siblings('div').removeClass('active');
	});
	/* 251210 글자·화면 설정 다크모드 선택 추가 end */

	/* // 20250625 GNB 화면/확대축소 설정(임정규) */


	// qucick menu
	/*
	$("#quick_menu").on({
		mouseover : function(){
			$(this).addClass("on");
			$(".quick_top").addClass("on");
		},
		mouseleave : function(){
			$(this).removeClass("on");
			$(".quick_top").removeClass("on");
		},
		focusin :  function(){
			$(this).addClass("on");
			$(".quick_top").addClass("on");
		},
		focusout : function(){
			$(this).removeClass("on");
			$(".quick_top").removeClass("on");
		},
	});
	*/

	// lnb 2depth
	$('.lnb > ul > li.depth > a').attr({'role': 'button', 'aria-expanded': 'false'});
	$('.lnb > ul > li.depth > a.on').attr('aria-expanded', 'true');
	$('.lnb > ul > li.depth > a').click(function(){
		var depth2 = $(this).hasClass('on');
		if(depth2){
			$(this).removeClass('on');
			$(this).siblings('ul').stop(true,true).slideUp();
            $(this).attr('aria-expanded', 'false');
		}else{
			$('.lnb ul > li.depth > a').removeClass('on').attr('aria-expanded', 'false');
			$('.lnb ul > li.depth > ul').stop().slideUp();
			$(this).addClass('on').attr('aria-expanded', 'true');;
			$(this).siblings('ul').stop(true,true).slideDown();
		}
	});
	// lnb 3depth
	$('.lnb > ul > li.depth > ul > li.depth > a').click(function(){
		$(this).attr('role', 'button');
		var depth3 = $(this).hasClass('on');
		if(depth3){
			$(this).removeClass('on');
			$(this).siblings('ul').stop(true,true).slideUp();
            $(this).attr('aria-expanded', 'true');
		}else{
			$('.lnb ul > li > ul > li.depth > a').removeClass('on');
			$('.lnb ul > li > ul > li.depth > ul').stop().slideUp();
			$(this).addClass('on');
			$(this).siblings('ul').stop(true,true).slideDown();
            $(this).attr('aria-expanded', 'false');
		}
	});

	// 스텝 프로그레스
	$("ul.form_progress > li.on").last().addClass("last-child");

	// 스크롤 이벤트
	$(".tab_title_wrap").length && ui.scrollEvent();

	// file uploading
	$('.box_file_progress > .close').click(function(){
		$('.box_file_progress').removeClass('on');
	});

	$({ val : 0 }).animate({ val : 100 }, {
		duration: 3000,
	   step: function() {
		 $(".progress_num").text(Math.floor(this.val));
	   },
	   complete: function() {
		 $(".progress_num").text(Math.floor(this.val));
		 $(".progress_num").css("color","#4D65E1");
	   }
	});

	$('.expend_btn_td > button').off('click').on('click', function() {
		if ($(this).hasClass('exp')) {
			$(this).parents('tr').nextAll('.expend_tr').hide();
			$(this).find('span').text('펼치기');
			$(this).removeClass('exp');
		} else {
			$(this).parents('tr').nextAll('.expend_tr').show();
			$(this).find('span').text('닫기');
			$(this).addClass('exp');
		}
	});

	$('.expend_ctr_btn .btn_ctr').off('click').on('click', function() {
		if ($(this).hasClass('exp')) {
			$(this).parents('tr').next('.expend_ctr').hide();
			$(this).find('span.blind').text('펼치기');
			$(this).removeClass('exp');
		} else {
			$(this).parents('tr').next('.expend_ctr').show();
			$(this).find('span.blind').text('닫기');
			$(this).addClass('exp');
		}
	});

	$('.btn_expand_section').off('click').on('click', function(){
		if($(this).hasClass('exp')){
			$(this).closest('.expand_section_wrap').find('.expand_content_area').hide();
			$(this).closest('.expand_section_wrap').removeClass('btn_expand_active');
			$(this).removeClass('exp').find('.blind').text('펼치기');
		}else{
			$(this).closest('.expand_section_wrap').find('.expand_content_area').show();
			$(this).closest('.expand_section_wrap').addClass('btn_expand_active');
			$(this).addClass('exp').find('.blind').text('닫기');
		}
	})

	$('.rdo_chk_expand.checked').each(function(){
		if($(this).is(':checked')){
			$(this).closest('.rdo_expand_group').next('.item').show();
			$(this).closest('.cell').next('.expand_check_area').show();
		}else{
			$(this).closest('.rdo_expand_group').next('.item').hide();
			$(this).closest('.cell').next('.expand_check_area').hide();
		}
	});
	$('.rdo_chk_expand').off('click').on('click', function(){
		if($(this).hasClass('checked')){
			$(this).closest('.rdo_expand_group').next('.item').show();
			$(this).closest('.cell').next('.expand_check_area').show();
		}else{
			$(this).closest('.rdo_expand_group').next('.item').hide();
			$(this).closest('.cell').next('.expand_check_area').hide();
		}
	});

	//마이페이지
	$('.my_info_area .mypage_toggle').click(function(){
		$(this).toggleClass('on');
	});

	$('.my_status_area').each(function() {
		const $this = $(this);
		var tabBtn = $this.find('.tab_wrap .tab_title > button');
		var tabCont = $this.find('.tab_wrap .status_cont');

		tabBtn.on('click', function() {
			var index = $(this).index();

			$(this).addClass('active');
			tabBtn.not($(this)).removeClass('active');
			tabCont.removeClass('active');
			tabCont.eq(index).addClass('active');
		});
	});

	// 이직 확인서 제출용
	$('.jobs_confirm .confirm').on('click', function() {
		var $this = $(this);
		if ($this.hasClass('type01')) {
			$this.removeClass('type01').addClass('type02').parent().find('.confirm_layer').hide();
		} else if ($this.hasClass('type02')) {
			$this.removeClass('type02').addClass('type01').parent().find('.confirm_layer').show();
		}
	});

	// 검색테이블 리스트
	let boxFormTable = $('article.box_form_content table').filter(function() {
        return $(this).find('input, select').length > 0 || $(this).hasClass('notCaption');
    });

	// 검색테이블 내 caption 삭제
	boxFormTable.find('caption').remove();

	// boxFormTable 리스트 중 검색테이블 내 th를 td.new_th로 변경
	for(let i = 0; i < boxFormTable.length; i++) {
		let th = boxFormTable[i].querySelectorAll('th');

		th.forEach(function(item){
			item.removeAttribute('scope');
			item.classList.add('new_th');
			let thAfter = item.outerHTML.replace("<th", "<td").replace("</th", "</td");
			item.outerHTML = thAfter;
		});
	}

	// tab keyboard action
	$(document).ready(function() {
		const $tabs = $('[role="tab"]');
		$tabs.on('keydown', function(e) {
			if(e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
				e.preventDefault();

				const currentIndex = $tabs.index(this);
				let nextIndex;

				if(e.key === 'ArrowRight') {
					nextIndex = (currentIndex + 1) % $tabs.length;
				} else {
					nextIndex = (currentIndex - 1 + $tabs.length) % $tabs.length;
				}

				$tabs.eq(nextIndex).focus();
			}
		});
	});

	// input[type="text"] placeholder와 title을 같게
	// let inputText = document.querySelectorAll('input[type="text"][placeholder]:not(:read-only):not(:disabled)');
	// inputText.forEach(function(item){
	// 	let inputTextPh = item.placeholder;
	// 	item.title = inputTextPh;
	// });

	// p태그 중 타이틀 역할인 것을 헤딩태그로 변경(p를 h3로 변경할 때만 가능)
	let pTitle = document.querySelectorAll('p.t2_sb, p.t1_sb, p.t3_sb');
	let uploadTl = document.querySelectorAll('p[class*="upload_tl"]');

	let changePArr = [pTitle, uploadTl]; //변경할 변수 배열

	for(let i = 0; i < changePArr.length; i++) {
		// console.log(changePArr[i]);

		changePArr[i].forEach(function(item){
			item.outerHTML = item.outerHTML.replace("<p", "<h3").replace("</p", "</h3");
		});
	}

	// link title 변경
	let linkText = document.querySelectorAll('a');
	linkText.forEach(function(item) {
		let titleAttr = item.getAttribute('title');
		// 링크에 btn_link class가 있거나 title에 새창이 있을 때 title을 새창 열림으로 변경
		if(item.classList.contains('btn_link') || (titleAttr && titleAttr.includes('새창') && !titleAttr.includes('새창 열림'))) {
			if(item.textContent !== "") {
				item.setAttribute('title', '새창 열림');
			}
		} else {
			if(item.textContent !== "") {
				//기존 가지고 있던 title의 값이 없으면 title 어트리뷰트 삭제.
				//기존은 아래 분기 없이 item.removeAttribute('title');
				//워크넷쪽 탭때문에 해당 분기 생성하였으나, 이슈 있을 시
				//item.parent(".tab_title")의 타이틀만 남겨두는식으로 접근 바람.
				if(item.hasAttribute("title")
				  &&(item.getAttribute("title") == "" || item.getAttribute("title") == null)){
					item.removeAttribute('title');
				}
			}
		}
	});

	/*챗봇 인풋 타이틀 추가
	let chatbot = document.querySelectorAll('div.chatbot-comeback');
	if(chatbot) {
		$("#chatbotSendmessage").attr("title", "챗봇 데이터 수집 메시지");
		$(".chatbot-comeback").removeClass("disabled");
		$(".chatbot-comeback").css("display", "block");
	}*/

	// select title 넣기
	let selectTag = document.querySelectorAll('select:not(label > select)');

	selectTag.forEach(function(item){
		if(!item.title) { //타이틀이 없을 때 작동
			if(item.id) { //아이디가 있을 때 작동
				let label = document.querySelector(`label[for="${item.id}"]`);
				if(!label) { //이어진 라벨이 없으면
					selectTitHanlder();
				}
			} else { //아이디도 없고 타이틀도 없으면
				selectTitHanlder();
			}
		}

		// 셀렉트에 타이틀 넣어주는 함수
		function selectTitHanlder (){
			let titValueArr = [
				/*
				{
					selText: "셀렉트 옵션에 들어가는 단어",
					selTit: '타이틀에 뭐라고 넣을지',
				},
				*/
				{
					selText: "씩", /* 10개씩, 20개씩이 들어간 셀렉트 */
					selTit: '단위를 선택해 주세요.',
				},
			]

			for(let i = 0; i < titValueArr.length; i++) {
				let selectOpTxt = item.querySelector('option').innerText.indexOf(`${titValueArr[i].selText}`);

				if(selectOpTxt > -1) {
					item.title = titValueArr[i].selTit;
					break;
				}
			}
		}
	});
});