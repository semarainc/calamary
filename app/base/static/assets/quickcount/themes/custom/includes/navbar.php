<header class="main-header">
  <nav class="navbar navbar-static-top">
    <div class="container">
      <div class="navbar-header">
        <a href="#" class="navbar-brand"><b>SISTEM</b>VOTING</a>
        <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar-collapse">
          <i class="fa fa-bars"></i>
        </button>
      </div>

      <!-- Collect the nav links, forms, and other content for toggling -->
      <div class="collapse navbar-collapse pull-left" id="navbar-collapse">
        <ul class="nav navbar-nav">
          <?php
            if(isset($_SESSION['student'])){
              echo "
                <li><a href='index.php'>HOME</a></li>
                <li><a href='transaction.php'>TRANSACTION</a></li>
              ";
            } 
          ?>
        </ul>
      </div>
      <!-- /.navbar-collapse -->
      <!-- Navbar Right Menu -->
      <div class="navbar-custom-menu">
        <ul class="nav navbar-nav">
          <li class="user user-menu">
            <a href="">
              <img src="<?php echo (!empty($voter['photo'])) ? 'themes/custom/images/'.$voter['photo'] : 'themes/custom/images/profile.jpg' ?>" class="user-image" alt="User Image">
              <span class="hidden-xs"><?php echo $voter['nama_lengkap']; ?></span>
            </a>
          </li>
          <li><a href="logout.php"><i class="fa fa-sign-out"></i> KELUAR</a></li>  
        </ul>
      </div>
      <!-- /.navbar-custom-menu -->
    </div>
    <!-- /.container-fluid -->
  </nav>
</header>