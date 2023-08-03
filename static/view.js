let page = 1;

function loadFiles() {
    $.get('/files?page=' + page, function(data) {
        $('#fileContainer').html(data);
        page++;

        let hasNextPage = $('#fileContainer').find('.next-page').length > 0;
        if (hasNextPage) {
            $('#loadMore').show();
        } else {
            $('#loadMore').hide();
        }
    });
}

$(document).ready(function() {
    $('#openModal').click(function() {
        loadFiles();
        $('#fileModal').modal();
    });

    $('#loadMore').click(function() {
        loadFiles();
    });

    $(document).on('click', '.download', function() {
        let fileId = $(this).data('id');
        $.ajax({
            url: '/download',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ fileId: fileId }),
            success: function(data) {
                window.open(data.downloadLink, '_blank');
            }
        });
    });
});
