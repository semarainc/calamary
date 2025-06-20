<!-- jQuery 3 -->
<script src="themes/custom/bower_components/jquery/dist/jquery.min.js"></script>
<!-- Bootstrap 3.3.7 -->
<script src="themes/custom/bower_components/bootstrap/dist/js/bootstrap.min.js"></script>
<!-- iCheck 1.0.1 -->
<script src="themes/custom/plugins/iCheck/icheck.min.js"></script>
<!-- DataTables -->
<script src="themes/custom/bower_components/datatables.net/js/jquery.dataTables.min.js"></script>
<script src="themes/custom/bower_components/datatables.net-bs/js/dataTables.bootstrap.min.js"></script>
<!-- SlimScroll -->
<script src="themes/custom/bower_components/jquery-slimscroll/jquery.slimscroll.min.js"></script>
<!-- FastClick -->
<script src="themes/custom/bower_components/fastclick/lib/fastclick.js"></script>
<!-- AdminLTE App -->
<script src="themes/custom/dist/js/adminlte.min.js"></script>
<!-- Data Table Initialize -->
<script>
  $(function () {
    $('#example1').DataTable()
  	var bookTable = $('#booklist').DataTable({
      'paging'      : true,
      'lengthChange': false,
      'searching'   : true,
      'ordering'    : true,
      'info'        : false,
      'autoWidth'   : false
    })

    $('#searchBox').on('keyup', function(){
    	bookTable.search(this.value).draw();
	});

  })
</script>