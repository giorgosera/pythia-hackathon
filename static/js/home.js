/**
 * @fileOverview This file contains all the JavaScript functionality for the home page.
 * 
 * @author <a href="mailto:hi@alexmic.net"> Alex Michael </a>
 */

CYP.onPageLoad(function() {
    
    
    
    // =============================== Listeners =============================== //
    
    
    
    $("#btnSearch").live("click", function() {
        var txt = $(this).attr("txtSearch");
        CYP.post("/keywords/send", {
            keywords: txt
        }, true, function(response) {
            if (response.s) {
                //CYP.fn.reloadPage();
 		CYP.successNotifier.show(response.feed);
            }
        });
    });
    
    
    // =============================== Initialization code =============================== //

    
    CYP.navigator.init();

});
