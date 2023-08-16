$(document).ready(function() {
    $('.procesos_form').hide();
});

$(document).ready(function() {
    $('#hide').on('change', function(){
        var selectValor = $(this).val();
            //console.log(selectValor)
        if (selectValor == 'Carta Procesos') {
            $('.procesos_form').show();
            $('#hospital').attr('required', 'required');
            $('#proceso').attr('required', 'required')
        }
        else if(selectValor == 'Carta General') {
            $('.procesos_form').hide();
            $('#hospital').attr('required', false);
            $('#proceso').attr('required', false)
        }
        else {
            $('.procesos_form').hide();
        }
    })
})